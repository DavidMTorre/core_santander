"""Orquestación del desembolso: solicitud -> crédito + cronograma -> desembolsado."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status

from app.repositories import rep_creditos, rep_solicitudes
from app.schemas.sch_desembolso import DesembolsoOut
from app.services import svc_desembolso

logger = logging.getLogger(__name__)

ESTADOS_DESEMBOLSABLES = ("aprobado", "condicionado")


def _monto_efectivo(solicitud: dict) -> Decimal:
    """Monto a desembolsar: aprobado -> solicitado; condicionado -> monto_aprobado."""
    if solicitud["estado"] == "condicionado":
        monto = solicitud.get("monto_aprobado")
        if monto is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La solicitud condicionada no tiene 'monto_aprobado'.",
            )
        return Decimal(str(monto))
    return Decimal(str(solicitud["monto_solicitado"]))


def desembolsar_solicitud(
    solicitud_id: str,
    fecha_desembolso: date | None = None,
    dia_pago: int | None = None,
) -> DesembolsoOut:
    """Crea el crédito, genera el cronograma y deja la solicitud en 'desembolsado'."""
    solicitud = rep_solicitudes.obtener_por_id(solicitud_id)

    if solicitud.get("estado") not in ESTADOS_DESEMBOLSABLES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud no está aprobada.",
        )

    monto = _monto_efectivo(solicitud)
    tea = Decimal(str(solicitud["tea_referencial"]))
    plazo = int(solicitud["plazo_meses"])

    fecha = fecha_desembolso or date.today()
    dia = dia_pago or fecha.day

    # Cronograma SIEMPRE sobre el monto efectivamente aprobado.
    datos = svc_desembolso.preparar_desembolso(monto, tea, plazo, fecha, dia)

    numero_credito = rep_creditos.generar_numero_credito()
    credito_data = {
        "cliente_id": solicitud["cliente_id"],
        "asesor_id": solicitud.get("asesor_id"),
        "agencia_id": solicitud.get("agencia_id"),
        "numero_credito": numero_credito,
        "monto_desembolsado": str(monto),
        "plazo_meses": plazo,
        "tea": str(tea),
        "garantia": solicitud.get("garantia") or "sin_garantia",
        "estado": "vigente",
        "fecha_desembolso": fecha.isoformat(),
        "fecha_vencimiento": datos["fecha_vencimiento"].isoformat(),
        "saldo_actual": str(monto),
        "cuotas_total": datos["cuotas_total"],
        "cuotas_pagadas": 0,
        "dias_mora": 0,
        "monto_vencido": 0,
    }

    # ORDEN: 1) crédito (se necesita su id), 2) cuotas, 3) marcar solicitud.
    credito = rep_creditos.crear_credito(credito_data)
    credito_id = str(credito["id"])

    try:
        rep_creditos.crear_cuotas_cronograma(
            credito_id, str(solicitud["cliente_id"]), datos["cronograma"]
        )
    except Exception as exc:  # noqa: BLE001 - se registra para evitar crédito huérfano
        logger.exception(
            "INCONSISTENCIA: crédito %s (%s) creado pero falló el cronograma. "
            "Revisar manualmente o reintentar la generación de cuotas.",
            numero_credito,
            credito_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Crédito {numero_credito} creado pero falló la generación del "
                f"cronograma. Revisar consistencia (crédito sin cuotas)."
            ),
        ) from exc

    rep_solicitudes.actualizar_estado(solicitud_id, "desembolsado")

    return DesembolsoOut(
        solicitud_id=solicitud_id,
        credito_id=credito_id,
        numero_credito=numero_credito,
        monto_desembolsado=monto,
        plazo_meses=plazo,
        cuotas_total=datos["cuotas_total"],
        cuota_mensual=datos["cuota_mensual"],
        fecha_desembolso=fecha,
        fecha_primera_cuota=datos["fecha_primera_cuota"],
        fecha_ultima_cuota=datos["fecha_ultima_cuota"],
        estado_solicitud="desembolsado",
    )
