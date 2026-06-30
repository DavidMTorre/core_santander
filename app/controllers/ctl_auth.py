"""Orquestación del login del cliente."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.deps import PERFILES_COMITE
from app.core.security import crear_access_token, hash_password, verify_password
from app.repositories import rep_auth
from app.schemas.sch_auth import RegistroClienteIn, TokenComiteOut, TokenOut


def login_cliente(usuario: str, password: str) -> TokenOut:
    """Valida credenciales del cliente y emite un JWT con el claim ``cliente_id``."""
    fila = rep_auth.obtener_auth_por_usuario(usuario)
    if not fila:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no registrado",
        )

    if fila.get("estado") != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no activo o bloqueado",
        )

    if not verify_password(password, fila.get("password_hash") or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
        )

    cliente_id = str(fila["cliente_id"])
    rep_auth.actualizar_ultimo_login(fila["id"])

    token = crear_access_token({"sub": usuario, "cliente_id": cliente_id})
    return TokenOut(access_token=token, cliente_id=cliente_id, usuario=usuario)


def registrar_cliente(payload: RegistroClienteIn) -> dict:
    """Crea credenciales para un cliente existente, hasheando con bcrypt ($2b$).

    El Core es el único que genera hashes, garantizando el formato $2b$ correcto
    (a diferencia de los seeds por SQL/pgcrypto que producen $2a$).
    """
    password_hash = hash_password(payload.password)
    fila = rep_auth.crear_auth_cliente(
        cliente_id=payload.cliente_id,
        usuario=payload.usuario,
        password_hash=password_hash,
    )
    # No se expone el password_hash en la respuesta.
    return {
        "id": fila.get("id"),
        "cliente_id": fila.get("cliente_id"),
        "usuario": fila.get("usuario"),
        "estado": fila.get("estado"),
    }


def login_comite(codigo_empleado: str, password: str) -> TokenComiteOut:
    """Valida credenciales del comité y emite un JWT con perfil/asesor_id.

    Solo entran perfiles de comité (supervisor/administrador); un operador -> 403.
    """
    fila = rep_auth.obtener_asesor_por_codigo(codigo_empleado)
    if not fila:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de empleado no registrado",
        )

    if not fila.get("activo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo o bloqueado",
        )

    perfil = fila.get("perfil")
    if perfil not in PERFILES_COMITE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado: se requiere perfil de comité",
        )

    if not verify_password(password, fila.get("password_hash") or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
        )

    asesor_id = str(fila["id"])
    token = crear_access_token(
        {
            "sub": codigo_empleado,
            "asesor_id": asesor_id,
            "perfil": perfil,
            "codigo_empleado": codigo_empleado,
        }
    )
    return TokenComiteOut(
        access_token=token,
        asesor_id=asesor_id,
        codigo_empleado=codigo_empleado,
        perfil=perfil,
    )
