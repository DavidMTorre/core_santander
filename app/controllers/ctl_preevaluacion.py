"""Orquestación de la pre-evaluación: solicitud + cliente + buró -> veredicto."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories import rep_clientes, rep_solicitudes
from app.schemas.sch_buro import BuroOut
from app.schemas.sch_preevaluacion import PreEvaluacionOut
from app.services import svc_buro, svc_preevaluacion


def preevaluar_solicitud(
    solicitud_id: str,
    cliente_autenticado: str | None = None,
) -> PreEvaluacionOut:
    """Combina capacidad de pago (ingreso/gasto/cuota) con el buró del cliente.

    Si se pasa ``cliente_autenticado``, verifica que la solicitud le pertenezca
    (evita que un cliente pre-evalúe la solicitud de otro) -> 403 en caso contrario.
    """
    solicitud = rep_solicitudes.obtener_por_id(solicitud_id)
    cliente_id = str(solicitud["cliente_id"])

    if cliente_autenticado is not None and cliente_id != cliente_autenticado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes pre-evaluar la solicitud de otro cliente.",
        )

    cliente = rep_clientes.obtener_cliente(cliente_id)

    pre = svc_preevaluacion.pre_evaluar(
        ingreso=cliente.get("ingresos_estimados"),
        gasto=solicitud.get("gastos_mensuales"),
        cuota_estimada=solicitud.get("cuota_estimada"),
    )

    try:
        buro = svc_buro.consultar_buro(cliente.get("numero_documento") or "")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return PreEvaluacionOut(
        veredicto=pre["veredicto"],
        puntaje=pre["puntaje"],
        disponible=pre["disponible"],
        ratio_cuota=pre["ratio_cuota"],
        buro=BuroOut(**buro),
    )
