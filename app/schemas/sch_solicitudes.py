"""Schemas Pydantic del flujo de solicitud de crédito."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SolicitudCrearIn(BaseModel):
    """Datos que envía el cliente para originar una solicitud.

    El ``cliente_id`` NO viaja en el body: se toma del JWT (claim cliente_id).
    """

    monto_solicitado: Decimal = Field(..., gt=0)
    plazo_meses: int = Field(..., gt=0)
    destino_credito: str
    garantia: str
    tipo_negocio: str | None = None
    nombre_negocio: str | None = None
    con_desgravamen: bool = True  # selecciona la TEA aplicable


class SolicitudOut(BaseModel):
    """Vista de salida de una solicitud (seguimiento del expediente)."""

    id: str
    numero_expediente: str | None = None
    cliente_id: str | None = None
    monto_solicitado: Decimal
    plazo_meses: int
    tea_referencial: Decimal | None = None
    cuota_estimada: Decimal | None = None
    estado: str
    canal: str | None = None
    created_at: datetime | None = None
