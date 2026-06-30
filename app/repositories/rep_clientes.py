"""Acceso a datos de clientes (tabla clientes).

Usa el cliente Supabase con service_role (se salta el RLS por diseño).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from supabase import Client

from app.db import get_supabase

TABLA = "clientes"


def obtener_cliente(cliente_id: str, db: Client | None = None) -> dict:
    """Devuelve datos básicos del cliente (404 si no existe)."""
    db = db or get_supabase()
    resp = (
        db.table(TABLA)
        .select("id, numero_documento, ingresos_estimados")
        .eq("id", cliente_id)
        .limit(1)
        .execute()
    )
    filas = resp.data or []
    if not filas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado.",
        )
    return filas[0]
