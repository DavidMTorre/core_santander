"""Schemas Pydantic del buró crediticio simulado."""

from __future__ import annotations

from pydantic import BaseModel


class BuroOut(BaseModel):
    """Resultado de una consulta de buró."""

    calificacion_sbs: str
    entidades_con_deuda: int
    deuda_total_pen: float
    mayor_deuda: float
    dias_mayor_mora: int
    inhabilitado: bool
