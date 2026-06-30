"""Seguridad: hashing de contraseñas (bcrypt) y emisión/validación de JWT.

El Core es el responsable de validar el login del cliente correctamente (la App
Clientes hoy compara en texto plano, lo cual es inseguro) y de emitir un JWT que
incluya el claim ``cliente_id`` que el RLS de Supabase espera (current_cliente_id()).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash.

    Compatibilidad con hashes generados fuera del Core:

    - Postgres/pgcrypto (``crypt(pass, gen_salt('bf'))``) produce hashes con
      prefijo ``$2a$``; otras librerías usan ``$2y$``. El algoritmo es idéntico al
      ``$2b$`` que genera la lib bcrypt de Python: solo cambia la etiqueta de
      versión. Sin normalizar, bcrypt lanza ``ValueError: Invalid salt`` y el
      login fallaría con 401 aunque la contraseña sea correcta. Por eso se
      normaliza el prefijo a ``$2b$`` antes de verificar.
    - Datos viejos en TEXTO PLANO (no empiezan con ``$2``): se comparan de forma
      directa como fallback para no romper accesos existentes.

    Cualquier excepción de bcrypt (incluida ``Invalid salt``) se traga y devuelve
    False de forma controlada: un hash malformado nunca debe reventar el login.

    TODO: migrar los registros en texto plano a bcrypt (re-hashear en el próximo
    login OK) y eliminar el fallback de texto plano cuando la migración termine.
    """
    if not hashed:
        return False

    if hashed.startswith("$2"):
        # Normalizar variantes $2a$ / $2y$ a $2b$ (misma KDF, otra etiqueta).
        if hashed.startswith(("$2a$", "$2y$")):
            hashed = "$2b$" + hashed[4:]
        try:
            return _pwd_context.verify(plain, hashed)
        except Exception:  # noqa: BLE001 - un hash malformado no debe romper el login
            return False

    # Fallback temporal para datos legados en texto plano.
    return plain == hashed


def crear_access_token(data: dict) -> str:
    """Crea un JWT firmado a partir de ``data``, agregando el claim ``exp``.

    El llamador es responsable de incluir ``cliente_id`` (str del UUID) y ``sub``
    (el usuario) dentro de ``data``.
    """
    settings = get_settings()
    to_encode = data.copy()
    expira = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode["exp"] = expira
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza ``jwt.PyJWTError`` si es inválido/expirado."""
    settings = get_settings()
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
