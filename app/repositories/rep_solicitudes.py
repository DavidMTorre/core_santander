"""Acceso a datos de solicitudes de crédito (tabla solicitudes_credito).

Usa el cliente Supabase con service_role (se salta el RLS por diseño).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from supabase import Client

from app.db import get_supabase

TABLA = "solicitudes_credito"

_MSG_NO_ENCONTRADA = "Solicitud no encontrada."


def obtener_asesor_id_de_cliente(cliente_id: str, db: Client | None = None) -> str | None:
    """Devuelve el ``asesor_id`` ya asignado al cliente en ``clientes``, o None."""
    db = db or get_supabase()
    resp = (
        db.table("clientes")
        .select("asesor_id")
        .eq("id", cliente_id)
        .limit(1)
        .execute()
    )
    filas = resp.data or []
    if not filas:
        return None
    return filas[0].get("asesor_id")


def crear_solicitud(data: dict, db: Client | None = None) -> dict:
    """Inserta una fila en ``solicitudes_credito`` y devuelve la fila creada."""
    db = db or get_supabase()
    resp = db.table(TABLA).insert(data).execute()
    filas = resp.data or []
    if not filas:
        raise RuntimeError("No se pudo crear la solicitud (respuesta vacía de Supabase).")
    return filas[0]


def obtener_por_id(solicitud_id: str, db: Client | None = None) -> dict:
    """Devuelve una solicitud por id (404 si no existe)."""
    db = db or get_supabase()
    resp = (
        db.table(TABLA)
        .select(
            "id, cliente_id, asesor_id, agencia_id, monto_solicitado, monto_aprobado, "
            "plazo_meses, cuota_estimada, tea_referencial, garantia, "
            "gastos_mensuales, ingresos_estimados, estado"
        )
        .eq("id", solicitud_id)
        .limit(1)
        .execute()
    )
    filas = resp.data or []
    if not filas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_MSG_NO_ENCONTRADA,
        )
    return filas[0]


def actualizar_resolucion(
    solicitud_id: str,
    estado: str,
    monto_aprobado: str | None = None,
    motivo_rechazo: str | None = None,
    condicion_adicional: str | None = None,
    db: Client | None = None,
) -> dict:
    """Actualiza el estado y los datos de resolución de una solicitud (404 si no existe).

    Estados válidos de resolución: 'aprobado', 'condicionado', 'rechazado'.
    """
    db = db or get_supabase()
    update = {
        "estado": estado,
        "monto_aprobado": monto_aprobado,
        "motivo_rechazo": motivo_rechazo,
        "condicion_adicional": condicion_adicional,
    }
    resp = db.table(TABLA).update(update).eq("id", solicitud_id).execute()
    filas = resp.data or []
    if not filas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_MSG_NO_ENCONTRADA,
        )
    return filas[0]


def actualizar_estado(solicitud_id: str, estado: str, db: Client | None = None) -> dict:
    """Actualiza solo el ``estado`` de una solicitud (404 si no existe)."""
    db = db or get_supabase()
    resp = db.table(TABLA).update({"estado": estado}).eq("id", solicitud_id).execute()
    filas = resp.data or []
    if not filas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_MSG_NO_ENCONTRADA,
        )
    return filas[0]


def listar_todas(estado: str | None = None, db: Client | None = None) -> list[dict]:
    """Lista TODAS las solicitudes (panel del comité), con filtro opcional por estado."""
    db = db or get_supabase()
    query = db.table(TABLA).select(
        "id, numero_expediente, cliente_id, monto_solicitado, plazo_meses, "
        "estado, cuota_estimada, created_at"
    )
    if estado:
        query = query.eq("estado", estado)
    resp = query.order("created_at", desc=True).execute()
    return resp.data or []


def listar_por_cliente(cliente_id: str, db: Client | None = None) -> list[dict]:
    """Lista las solicitudes de un cliente, más recientes primero."""
    db = db or get_supabase()
    resp = (
        db.table(TABLA)
        .select("*")
        .eq("cliente_id", cliente_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []
