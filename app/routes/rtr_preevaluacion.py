"""Rutas de la pre-evaluación crediticia."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.controllers import ctl_preevaluacion
from app.core.deps import get_current_cliente_o_comite
from app.schemas.sch_preevaluacion import PreEvaluacionOut

router = APIRouter(prefix="/preevaluacion", tags=["preevaluacion"])


@router.get("/{solicitud_id}")
def preevaluar(
    solicitud_id: str,
    auth: Annotated[dict, Depends(get_current_cliente_o_comite)],
) -> PreEvaluacionOut:
    """Pre-evalúa una solicitud.

    El comité puede ver cualquiera; el cliente solo la suya (ownership en el controller).
    """
    cliente_autenticado = None if auth["es_comite"] else auth["cliente_id"]
    return ctl_preevaluacion.preevaluar_solicitud(
        solicitud_id, cliente_autenticado=cliente_autenticado
    )
