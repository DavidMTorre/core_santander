"""Dependencias de FastAPI para proteger endpoints con JWT (cliente y comité)."""

from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decodificar_token

_bearer_scheme = HTTPBearer(auto_error=True)

# Perfiles de asesores_negocio autorizados a actuar como comité.
PERFILES_COMITE = ("supervisor", "administrador")


def _decodificar_o_401(token: str) -> dict:
    """Decodifica el JWT o lanza 401 (expirado / inválido)."""
    try:
        return decodificar_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_cliente(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """Valida el Bearer token y devuelve el ``cliente_id`` del claim."""
    payload = _decodificar_o_401(credentials.credentials)
    cliente_id = payload.get("cliente_id")
    if not cliente_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin cliente_id",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(cliente_id)


def get_current_comite(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """Valida el Bearer token y exige perfil de comité (supervisor/administrador).

    Returns:
        dict con ``asesor_id``, ``perfil`` y ``codigo_empleado``.
    """
    payload = _decodificar_o_401(credentials.credentials)

    perfil = payload.get("perfil")
    if perfil not in PERFILES_COMITE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado: se requiere perfil de comité",
        )

    asesor_id = payload.get("asesor_id")
    if not asesor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin asesor_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "asesor_id": str(asesor_id),
        "perfil": perfil,
        "codigo_empleado": payload.get("codigo_empleado"),
    }
