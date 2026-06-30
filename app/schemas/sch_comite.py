"""Schemas Pydantic de la decisión de comité."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class ResolucionComiteIn(BaseModel):
    """Resolución que registra el comité sobre un expediente."""

    decision: Literal["aprobado", "condicionado", "rechazado"]
    monto_aprobado: Decimal | None = None
    motivo_rechazo: str | None = None
    condicion_adicional: str | None = None


class DecisionOut(BaseModel):
    """Estado resultante de la solicitud tras la resolución del comité."""

    solicitud_id: str
    estado: str
    monto_aprobado: Decimal | None = None
    motivo_rechazo: str | None = None
    condicion_adicional: str | None = None
    forzado: bool = False  # True si la regla de seguridad forzó el rechazo
