"""Schemas Pydantic para la autenticación."""

from __future__ import annotations

from pydantic import BaseModel


class LoginClienteIn(BaseModel):
    """Credenciales de login del cliente."""

    usuario: str
    password: str


class RegistroClienteIn(BaseModel):
    """Datos para crear credenciales de un cliente ya existente en ``clientes``."""

    cliente_id: str  # UUID del cliente existente
    usuario: str
    password: str


class LoginComiteIn(BaseModel):
    """Credenciales de login del comité (panel web)."""

    codigo_empleado: str
    password: str


class TokenComiteOut(BaseModel):
    """Respuesta con el token de acceso del comité."""

    access_token: str
    token_type: str = "bearer"
    asesor_id: str
    codigo_empleado: str
    perfil: str


class TokenOut(BaseModel):
    """Respuesta con el token de acceso emitido."""

    access_token: str
    token_type: str = "bearer"
    cliente_id: str
    usuario: str
