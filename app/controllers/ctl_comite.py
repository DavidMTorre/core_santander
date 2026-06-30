"""Orquestación de la decisión de comité: sugerencia automática y resolución final."""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status

from app.controllers import ctl_preevaluacion
from app.repositories import rep_clientes, rep_solicitudes
from app.schemas.sch_comite import DecisionOut, ResolucionComiteIn
from app.schemas.sch_solicitudes import SolicitudOut
from app.services import svc_buro, svc_comite

# Buró que descalifica cualquier aprobación (casos 28/29/30).
_CALIF_NO_APTAS = ("DUDOSO", "PERDIDA")


def listar_solicitudes(estado: str | None = None) -> list[SolicitudOut]:
    """Lista TODAS las solicitudes para el panel del comité (filtro opcional por estado)."""
    filas = rep_solicitudes.listar_todas(estado)
    return [SolicitudOut(**f) for f in filas]


def obtener_sugerencia(solicitud_id: str) -> dict:
    """Corre buró + pre-evaluación + sugerir_decision. No persiste nada."""
    pre = ctl_preevaluacion.preevaluar_solicitud(solicitud_id)
    buro = pre.buro.model_dump()
    preeval = {"veredicto": pre.veredicto, "puntaje": pre.puntaje}

    sugerencia = svc_comite.sugerir_decision(buro, preeval)

    # Para APROBADO, el monto sugerido es el solicitado completo.
    if sugerencia["sugerencia"] == svc_comite.SUGERENCIA_APROBADO and sugerencia.get("monto_sugerido") is None:
        solicitud = rep_solicitudes.obtener_por_id(solicitud_id)
        monto = solicitud.get("monto_solicitado")
        sugerencia["monto_sugerido"] = float(monto) if monto is not None else None

    return sugerencia


def _buro_descalifica(buro: dict) -> tuple[bool, str | None]:
    """Indica si el buró impide aprobar y, en tal caso, el motivo del rechazo."""
    if buro.get("inhabilitado"):
        return True, "En lista de inhabilitados del sistema financiero"
    calificacion = buro.get("calificacion_sbs")
    if calificacion in _CALIF_NO_APTAS:
        return True, f"Calificación SBS no apta ({calificacion}) con mora vigente"
    return False, None


def _error_422(detalle: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detalle)


def _construir_resolucion(
    payload: ResolucionComiteIn, monto_solicitado: Decimal
) -> tuple[str, Decimal | None, str | None, str | None]:
    """Valida coherencia y devuelve (estado, monto_aprobado, motivo, condicion)."""
    if payload.decision == "aprobado":
        return "aprobado", monto_solicitado, None, None

    if payload.decision == "condicionado":
        if payload.monto_aprobado is None:
            raise _error_422("Un condicionado requiere 'monto_aprobado'.")
        monto = Decimal(str(payload.monto_aprobado))
        if monto >= monto_solicitado:
            raise _error_422(
                "En un condicionado, 'monto_aprobado' debe ser menor al solicitado."
            )
        if not (payload.condicion_adicional and payload.condicion_adicional.strip()):
            raise _error_422("Un condicionado requiere 'condicion_adicional'.")
        return "condicionado", monto, None, payload.condicion_adicional

    # rechazado
    if not (payload.motivo_rechazo and payload.motivo_rechazo.strip()):
        raise _error_422("Un rechazo requiere 'motivo_rechazo'.")
    return "rechazado", None, payload.motivo_rechazo, None


def resolver_solicitud(solicitud_id: str, payload: ResolucionComiteIn) -> DecisionOut:
    """Valida coherencia y persiste el estado final del expediente.

    Regla de seguridad: si el buró es inhabilitado o DUDOSO/PERDIDA, NO se puede
    aprobar ni condicionar; se fuerza el rechazo aunque el comité intente aprobar.
    """
    solicitud = rep_solicitudes.obtener_por_id(solicitud_id)
    monto_solicitado = Decimal(str(solicitud["monto_solicitado"]))

    cliente = rep_clientes.obtener_cliente(str(solicitud["cliente_id"]))
    buro = svc_buro.consultar_buro(cliente.get("numero_documento") or "")

    descalifica, motivo_buro = _buro_descalifica(buro)

    # Regla de seguridad: forzar rechazo ante intento de aprobar/condicionar.
    if descalifica and payload.decision in ("aprobado", "condicionado"):
        estado, monto_aprobado, motivo_rechazo, condicion_adicional = (
            "rechazado",
            None,
            motivo_buro,
            None,
        )
        forzado = True
    else:
        estado, monto_aprobado, motivo_rechazo, condicion_adicional = _construir_resolucion(
            payload, monto_solicitado
        )
        forzado = False

    fila = rep_solicitudes.actualizar_resolucion(
        solicitud_id,
        estado=estado,
        monto_aprobado=str(monto_aprobado) if monto_aprobado is not None else None,
        motivo_rechazo=motivo_rechazo,
        condicion_adicional=condicion_adicional,
    )

    return DecisionOut(
        solicitud_id=solicitud_id,
        estado=fila.get("estado", estado),
        monto_aprobado=monto_aprobado,
        motivo_rechazo=motivo_rechazo,
        condicion_adicional=condicion_adicional,
        forzado=forzado,
    )
