"""Rutas del buró crediticio simulado."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers import ctl_buro
from app.core.deps import get_current_cliente_o_comite
from app.schemas.sch_buro import BuroOut

router = APIRouter(prefix="/buro", tags=["buro"])


@router.get("/{cliente_id}")
def consultar_buro(
    cliente_id: str,
    auth: Annotated[dict, Depends(get_current_cliente_o_comite)],
) -> BuroOut:
    """Consulta el buró de un cliente.

    El comité puede consultar cualquiera; el cliente solo el suyo (ownership).
    """
    if not auth["es_comite"] and cliente_id != auth["cliente_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes consultar el buró de otro cliente.",
        )
    return ctl_buro.consultar_buro_cliente(cliente_id)
