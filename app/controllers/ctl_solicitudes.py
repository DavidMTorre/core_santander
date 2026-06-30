"""Orquestación del flujo de creación/listado de solicitudes del cliente."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.config import get_settings
from app.repositories import rep_solicitudes
from app.schemas.sch_solicitudes import SolicitudCrearIn, SolicitudOut
from app.services import svc_solicitudes


def resolver_asesor_id(cliente_id: str) -> str:
    """Resuelve el ``asesor_id`` (NOT NULL) para una solicitud del cliente.

    Estrategia (confirmada): usar el asesor ya asignado al cliente; si no tiene,
    caer al asesor "SIN_ASIGNAR" configurado en ``.env`` (ASESOR_SIN_ASIGNAR_ID).
    Si no hay ninguno de los dos, no se inventa: se devuelve un error claro.
    """
    asesor_id = rep_solicitudes.obtener_asesor_id_de_cliente(cliente_id)
    if asesor_id:
        return str(asesor_id)

    fallback = get_settings().ASESOR_SIN_ASIGNAR_ID
    if fallback:
        return str(fallback)

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            "El cliente no tiene asesor asignado y no hay ASESOR_SIN_ASIGNAR_ID "
            "configurado en el entorno."
        ),
    )


def crear_solicitud_cliente(cliente_id: str, payload: SolicitudCrearIn) -> SolicitudOut:
    """Prepara, resuelve asesor e inserta la solicitud; devuelve la fila creada."""
    data = svc_solicitudes.preparar_solicitud(cliente_id, payload)
    data["asesor_id"] = resolver_asesor_id(cliente_id)
    fila = rep_solicitudes.crear_solicitud(data)
    return SolicitudOut(**fila)


def listar_mias(cliente_id: str) -> list[SolicitudOut]:
    """Lista las solicitudes del cliente autenticado."""
    filas = rep_solicitudes.listar_por_cliente(cliente_id)
    return [SolicitudOut(**f) for f in filas]
