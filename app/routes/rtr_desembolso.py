"""Rutas del desembolso (lado comité/asesor; auth de asesor pendiente)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.controllers import ctl_desembolso
from app.core.deps import get_current_comite
from app.schemas.sch_desembolso import DesembolsoIn, DesembolsoOut

router = APIRouter(prefix="/desembolso", tags=["desembolso"])


@router.post("/{solicitud_id}")
def desembolsar(
    solicitud_id: str,
    _comite: Annotated[dict, Depends(get_current_comite)],
    payload: DesembolsoIn | None = None,
) -> DesembolsoOut:
    """Desembolsa una solicitud aprobada/condicionada: crea crédito + cronograma."""
    payload = payload or DesembolsoIn()
    return ctl_desembolso.desembolsar_solicitud(
        solicitud_id,
        fecha_desembolso=payload.fecha_desembolso,
        dia_pago=payload.dia_pago,
    )
