"""Acceso a datos del buró: documento del cliente y registro de consultas.

Usa el cliente Supabase con service_role (se salta el RLS por diseño).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from supabase import Client

from app.db import get_supabase

TABLA = "consultas_buro"


def obtener_documento_de_cliente(cliente_id: str, db: Client | None = None) -> str:
    """Lee ``numero_documento`` de ``clientes``. 404 si no existe; 409 si está vacío."""
    db = db or get_supabase()
    resp = (
        db.table("clientes")
        .select("numero_documento")
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

    documento = filas[0].get("numero_documento")
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El cliente no tiene número de documento registrado.",
        )
    return str(documento)


def registrar_consulta_buro(data: dict, db: Client | None = None) -> dict:
    """Inserta una fila de evidencia en ``consultas_buro`` y la devuelve."""
    db = db or get_supabase()
    resp = db.table(TABLA).insert(data).execute()
    filas = resp.data or []
    return filas[0] if filas else {}
