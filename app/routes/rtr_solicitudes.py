"""Rutas del flujo de solicitud de crédito (rol cliente)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.controllers import ctl_solicitudes
from app.core.deps import get_current_cliente
from app.schemas.sch_solicitudes import SolicitudCrearIn, SolicitudOut

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_solicitud(
    payload: SolicitudCrearIn,
    cliente_id: Annotated[str, Depends(get_current_cliente)],
) -> SolicitudOut:
    """Crea una solicitud. El ``cliente_id`` se toma del JWT, no del body."""
    return ctl_solicitudes.crear_solicitud_cliente(cliente_id, payload)


@router.get("/mias")
def listar_mias(
    cliente_id: Annotated[str, Depends(get_current_cliente)],
) -> list[SolicitudOut]:
    """Lista las solicitudes del cliente autenticado (seguimiento del expediente)."""
    return ctl_solicitudes.listar_mias(cliente_id)
