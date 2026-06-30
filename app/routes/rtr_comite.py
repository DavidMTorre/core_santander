"""Rutas de la decisión de comité (protegidas con auth de comité)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.controllers import ctl_comite
from app.core.deps import get_current_comite
from app.schemas.sch_comite import DecisionOut, ResolucionComiteIn
from app.schemas.sch_solicitudes import SolicitudOut

router = APIRouter(prefix="/comite", tags=["comite"])


@router.get("/solicitudes")
def listar_solicitudes(
    _comite: Annotated[dict, Depends(get_current_comite)],
    estado: str | None = None,
) -> list[SolicitudOut]:
    """Panel: lista TODAS las solicitudes, con filtro opcional ?estado=."""
    return ctl_comite.listar_solicitudes(estado)


@router.get("/{solicitud_id}/sugerencia")
def obtener_sugerencia(
    solicitud_id: str,
    _comite: Annotated[dict, Depends(get_current_comite)],
) -> dict:
    """Devuelve la sugerencia automática (buró + pre-evaluación). No persiste."""
    return ctl_comite.obtener_sugerencia(solicitud_id)


@router.post("/{solicitud_id}/resolver")
def resolver(
    solicitud_id: str,
    _comite: Annotated[dict, Depends(get_current_comite)],
    payload: ResolucionComiteIn,
) -> DecisionOut:
    """Registra la decisión final del comité y persiste el estado del expediente."""
    return ctl_comite.resolver_solicitud(solicitud_id, payload)
