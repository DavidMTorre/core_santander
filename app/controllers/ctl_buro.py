"""Orquestación de la consulta de buró: documento -> cálculo -> evidencia."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.controllers.ctl_solicitudes import resolver_asesor_id
from app.repositories import rep_buro
from app.schemas.sch_buro import BuroOut
from app.services import svc_buro


def consultar_buro_cliente(cliente_id: str) -> BuroOut:
    """Resuelve el documento, calcula el buró y registra la consulta como evidencia."""
    documento = rep_buro.obtener_documento_de_cliente(cliente_id)

    try:
        resultado = svc_buro.consultar_buro(documento)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # asesor_id es NOT NULL en consultas_buro: mismo criterio que en solicitudes.
    asesor_id = resolver_asesor_id(cliente_id)

    rep_buro.registrar_consulta_buro(
        {
            "asesor_id": asesor_id,
            "cliente_id": cliente_id,
            "dni_consultado": documento,
            "calificacion_sbs": resultado["calificacion_sbs"],
            "entidades_con_deuda": resultado["entidades_con_deuda"],
            "deuda_total_pen": resultado["deuda_total_pen"],
            "mayor_deuda": resultado["mayor_deuda"],
            "dias_mayor_mora": resultado["dias_mayor_mora"],
            "resultado_json": resultado,
        }
    )

    return BuroOut(**resultado)
