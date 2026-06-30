"""Acceso a datos de autenticación del cliente (tabla cliente_app_auth).

Usa el cliente Supabase con service_role (se salta el RLS por diseño).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from supabase import Client

from app.db import get_supabase

TABLA = "cliente_app_auth"


def obtener_auth_por_usuario(usuario: str, db: Client | None = None) -> dict | None:
    """Devuelve la fila de ``cliente_app_auth`` para ``usuario``, o None si no existe."""
    db = db or get_supabase()
    resp = (
        db.table(TABLA)
        .select("id, cliente_id, usuario, password_hash, estado, ultimo_login")
        .eq("usuario", usuario)
        .limit(1)
        .execute()
    )
    filas = resp.data or []
    return filas[0] if filas else None


def obtener_asesor_por_codigo(
    codigo_empleado: str, db: Client | None = None
) -> dict | None:
    """Devuelve la fila de ``asesores_negocio`` por código de empleado, o None."""
    db = db or get_supabase()
    resp = (
        db.table("asesores_negocio")
        .select("id, codigo_empleado, nombres, apellidos, perfil, activo, password_hash")
        .eq("codigo_empleado", codigo_empleado)
        .limit(1)
        .execute()
    )
    filas = resp.data or []
    return filas[0] if filas else None


def actualizar_ultimo_login(auth_id: str, db: Client | None = None) -> None:
    """Marca ``ultimo_login`` con la fecha/hora actual (UTC)."""
    db = db or get_supabase()
    db.table(TABLA).update(
        {"ultimo_login": datetime.now(timezone.utc).isoformat()}
    ).eq("id", auth_id).execute()


def crear_auth_cliente(
    cliente_id: str,
    usuario: str,
    password_hash: str,
    db: Client | None = None,
) -> dict:
    """Inserta credenciales en ``cliente_app_auth`` y devuelve la fila creada.

    La columna ``usuario`` es UNIQUE: si ya existe, Supabase responde con un error
    de clave duplicada (código Postgres 23505) que se traduce a HTTP 409.
    """
    db = db or get_supabase()
    payload = {
        "cliente_id": cliente_id,
        "usuario": usuario,
        "password_hash": password_hash,
        "estado": "activo",
    }
    try:
        resp = db.table(TABLA).insert(payload).execute()
    except Exception as exc:  # noqa: BLE001 - se inspecciona y se re-traduce
        if _es_error_usuario_duplicado(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El usuario '{usuario}' ya está registrado.",
            ) from exc
        raise

    filas = resp.data or []
    if not filas:
        raise RuntimeError("No se pudo crear el usuario (respuesta vacía de Supabase).")
    return filas[0]


def _es_error_usuario_duplicado(exc: Exception) -> bool:
    """Detecta el error de UNIQUE violada (Postgres 23505) en la excepción."""
    texto = str(getattr(exc, "message", "") or "") + " " + str(exc)
    codigo = str(getattr(exc, "code", "") or "")
    return "23505" in texto or codigo == "23505" or "duplicate key" in texto.lower()
