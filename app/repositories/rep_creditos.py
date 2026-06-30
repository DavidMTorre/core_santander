"""Acceso a datos de créditos y cronograma de cuotas.

Usa el cliente Supabase con service_role (escritura exclusiva del Core, según M6).
"""

from __future__ import annotations

import random
from collections.abc import Iterable
from datetime import datetime, timezone

from supabase import Client

from app.db import get_supabase
from app.services.credito import Cuota

TABLA_CREDITOS = "creditos"
TABLA_CRONOGRAMA = "cronograma_cuotas"


def generar_numero_credito(momento: datetime | None = None) -> str:
    """Genera un número de crédito con formato ``CRE-YYYYMMDD-NNNN`` (UQ en el esquema)."""
    momento = momento or datetime.now(timezone.utc)
    sufijo = f"{random.randint(0, 9999):04d}"
    return f"CRE-{momento:%Y%m%d}-{sufijo}"


def crear_credito(data: dict, db: Client | None = None) -> dict:
    """Inserta una fila en ``creditos`` y devuelve el crédito creado (con su id)."""
    db = db or get_supabase()
    resp = db.table(TABLA_CREDITOS).insert(data).execute()
    filas = resp.data or []
    if not filas:
        raise RuntimeError("No se pudo crear el crédito (respuesta vacía de Supabase).")
    return filas[0]


def crear_cuotas_cronograma(
    credito_id: str,
    cliente_id: str,
    cuotas: Iterable[Cuota],
    db: Client | None = None,
) -> list[dict]:
    """Inserta el cronograma en ``cronograma_cuotas`` respetando los CHECK del esquema.

    Mapea cada ``Cuota`` del motor a las columnas reales e incluye el ``cliente_id``
    denormalizado (obligatorio según la nota 10 del esquema).
    """
    db = db or get_supabase()
    filas = [
        {
            "credito_id": credito_id,
            "cliente_id": cliente_id,  # denormalizado (nota 10)
            "numero_cuota": c.numero,  # > 0
            "fecha_vencimiento": c.fecha_pago.isoformat(),
            "monto_cuota": str(c.cuota),
            "monto_capital": str(c.capital),
            "monto_interes": str(c.interes),
            "saldo_capital": str(c.saldo),
            "estado": "pendiente",
        }
        for c in cuotas
    ]
    resp = db.table(TABLA_CRONOGRAMA).insert(filas).execute()
    return resp.data or []
