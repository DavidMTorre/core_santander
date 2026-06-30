"""Schemas Pydantic del desembolso."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class DesembolsoIn(BaseModel):
    """Parámetros del desembolso. Si se omiten, se usan la fecha actual y su día."""

    fecha_desembolso: date | None = None
    dia_pago: int | None = Field(default=None, ge=1, le=31)


class DesembolsoOut(BaseModel):
    """Resumen del crédito creado y su cronograma."""

    solicitud_id: str
    credito_id: str
    numero_credito: str | None = None
    monto_desembolsado: Decimal
    plazo_meses: int
    cuotas_total: int
    cuota_mensual: Decimal
    fecha_desembolso: date
    fecha_primera_cuota: date
    fecha_ultima_cuota: date
    estado_solicitud: str = "desembolsado"
