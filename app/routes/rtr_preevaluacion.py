"""Rutas de la pre-evaluación crediticia."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.controllers import ctl_preevaluacion
from app.core.deps import get_current_cliente
from app.schemas.sch_preevaluacion import PreEvaluacionOut

router = APIRouter(prefix="/preevaluacion", tags=["preevaluacion"])


@router.get("/{solicitud_id}")
def preevaluar(
    solicitud_id: str,
    cliente_autenticado: Annotated[str, Depends(get_current_cliente)],
) -> PreEvaluacionOut:
    """Pre-evalúa una solicitud. Solo el cliente dueño de la solicitud puede verla."""
    return ctl_preevaluacion.preevaluar_solicitud(
        solicitud_id, cliente_autenticado=cliente_autenticado
    )
