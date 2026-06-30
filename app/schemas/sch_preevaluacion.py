"""Schemas Pydantic de la pre-evaluación crediticia."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.sch_buro import BuroOut


class PreEvaluacionOut(BaseModel):
    """Resultado combinado: capacidad de pago + buró embebido."""

    veredicto: str
    puntaje: int
    disponible: float
    ratio_cuota: float | None = None
    buro: BuroOut | None = None
