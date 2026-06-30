"""Tests de la capa de seguridad (funciones puras, sin tocar Supabase)."""

import jwt
import pytest

from app.core.security import (
    crear_access_token,
    decodificar_token,
    hash_password,
    verify_password,
)


def test_hash_verify_roundtrip():
    hashed = hash_password("SuperSecreta123")
    assert hashed.startswith("$2")  # formato bcrypt
    assert hashed != "SuperSecreta123"
    assert verify_password("SuperSecreta123", hashed) is True
    assert verify_password("incorrecta", hashed) is False


def test_fallback_texto_plano():
    # Registro legado con contraseña en texto plano (sin formato bcrypt).
    assert verify_password("clientedemo", "clientedemo") is True
    assert verify_password("otra", "clientedemo") is False


def test_verify_hash_postgres_2a():
    # Hash $2a$ generado por pgcrypto (crypt + gen_salt('bf')) para 'demo1234'.
    hash_2a = "$2a$06$SHPnt4Ame0ieGHhY3gOV0.DX4D1elzDzhs0t7IkYm.95oe5Y2zNVu"
    assert verify_password("demo1234", hash_2a) is True
    assert verify_password("incorrecta", hash_2a) is False


def test_verify_hash_2y_no_revienta():
    # Un $2y$ malformado no debe reventar el login: devuelve False controlado.
    assert verify_password("x", "$2y$06$saltinvalido") is False


def test_verify_password_hash_vacio():
    assert verify_password("loquesea", "") is False


def test_token_preserva_cliente_id():
    cid = "11111111-1111-1111-1111-111111111111"
    token = crear_access_token({"sub": "usuario1", "cliente_id": cid})
    payload = decodificar_token(token)
    assert payload["cliente_id"] == cid
    assert payload["sub"] == "usuario1"
    assert "exp" in payload


def test_token_invalido_falla():
    with pytest.raises(jwt.PyJWTError):
        decodificar_token("token.basura.invalido")
