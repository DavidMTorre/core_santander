"""Rutas de autenticación."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.controllers import ctl_auth
from app.schemas.sch_auth import (
    LoginClienteIn,
    LoginComiteIn,
    RegistroClienteIn,
    TokenComiteOut,
    TokenOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/cliente/login")
def login_cliente(payload: LoginClienteIn) -> TokenOut:
    """Login del cliente: valida usuario/contraseña y devuelve un JWT.

    Devuelve 401 si las credenciales son inválidas, 403 si el usuario no está activo.
    """
    return ctl_auth.login_cliente(payload.usuario, payload.password)


@router.post("/cliente/registrar", status_code=status.HTTP_201_CREATED)
def registrar_cliente(payload: RegistroClienteIn) -> dict:
    """Crea credenciales de cliente con hash bcrypt ($2b$). 409 si el usuario existe."""
    return ctl_auth.registrar_cliente(payload)


@router.post("/comite/login")
def login_comite(payload: LoginComiteIn) -> TokenComiteOut:
    """Login del comité (panel web). Solo perfiles supervisor/administrador.

    401 si credenciales inválidas; 403 si el perfil no es de comité o está inactivo.
    """
    return ctl_auth.login_comite(payload.codigo_empleado, payload.password)
