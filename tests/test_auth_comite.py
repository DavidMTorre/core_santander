"""Tests de la autenticación del comité (sin tocar Supabase)."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.controllers import ctl_auth
from app.core import deps
from app.core.security import crear_access_token, decodificar_token, hash_password
from app.repositories import rep_auth


def _fake_asesor(perfil="supervisor", activo=True, password="claveComite"):
    return {
        "id": "asesor-1",
        "codigo_empleado": "COMITE01",
        "nombres": "Ana",
        "apellidos": "Comité",
        "perfil": perfil,
        "activo": activo,
        "password_hash": hash_password(password),
    }


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_login_operador_403(monkeypatch):
    monkeypatch.setattr(
        rep_auth, "obtener_asesor_por_codigo",
        lambda c: _fake_asesor(perfil="operador"),
    )
    with pytest.raises(HTTPException) as exc:
        ctl_auth.login_comite("COMITE01", "claveComite")
    assert exc.value.status_code == 403


def test_login_supervisor_ok(monkeypatch):
    monkeypatch.setattr(
        rep_auth, "obtener_asesor_por_codigo",
        lambda c: _fake_asesor(perfil="supervisor"),
    )
    out = ctl_auth.login_comite("COMITE01", "claveComite")
    assert out.perfil == "supervisor"
    assert out.codigo_empleado == "COMITE01"
    assert out.asesor_id == "asesor-1"
    payload = decodificar_token(out.access_token)
    assert payload["perfil"] == "supervisor"
    assert payload["asesor_id"] == "asesor-1"
    assert payload["codigo_empleado"] == "COMITE01"


def test_login_clave_incorrecta_401(monkeypatch):
    monkeypatch.setattr(
        rep_auth, "obtener_asesor_por_codigo",
        lambda c: _fake_asesor(perfil="supervisor", password="correcta"),
    )
    with pytest.raises(HTTPException) as exc:
        ctl_auth.login_comite("COMITE01", "incorrecta")
    assert exc.value.status_code == 401


def test_login_no_existe_401(monkeypatch):
    monkeypatch.setattr(rep_auth, "obtener_asesor_por_codigo", lambda c: None)
    with pytest.raises(HTTPException) as exc:
        ctl_auth.login_comite("NOEXISTE", "x")
    assert exc.value.status_code == 401


def test_login_inactivo_403(monkeypatch):
    monkeypatch.setattr(
        rep_auth, "obtener_asesor_por_codigo",
        lambda c: _fake_asesor(perfil="supervisor", activo=False),
    )
    with pytest.raises(HTTPException) as exc:
        ctl_auth.login_comite("COMITE01", "claveComite")
    assert exc.value.status_code == 403


def test_get_current_comite_acepta_supervisor():
    token = crear_access_token(
        {"sub": "COMITE01", "asesor_id": "asesor-1", "perfil": "supervisor",
         "codigo_empleado": "COMITE01"}
    )
    comite = deps.get_current_comite(_creds(token))
    assert comite["perfil"] == "supervisor"
    assert comite["asesor_id"] == "asesor-1"


def test_get_current_comite_rechaza_operador():
    token = crear_access_token(
        {"sub": "X", "asesor_id": "a", "perfil": "operador", "codigo_empleado": "X"}
    )
    with pytest.raises(HTTPException) as exc:
        deps.get_current_comite(_creds(token))
    assert exc.value.status_code == 403


def test_get_current_comite_rechaza_token_de_cliente():
    # Un token de cliente (sin perfil) no debe pasar como comité.
    token = crear_access_token({"sub": "user1", "cliente_id": "cli-1"})
    with pytest.raises(HTTPException) as exc:
        deps.get_current_comite(_creds(token))
    assert exc.value.status_code == 403


def test_cliente_o_comite_acepta_comite():
    token = crear_access_token(
        {"sub": "C", "asesor_id": "a1", "perfil": "administrador", "codigo_empleado": "C"}
    )
    auth = deps.get_current_cliente_o_comite(_creds(token))
    assert auth["es_comite"] is True
    assert auth["cliente_id"] is None


def test_cliente_o_comite_acepta_cliente():
    token = crear_access_token({"sub": "user1", "cliente_id": "cli-1"})
    auth = deps.get_current_cliente_o_comite(_creds(token))
    assert auth["es_comite"] is False
    assert auth["cliente_id"] == "cli-1"


def test_cliente_o_comite_rechaza_token_vacio():
    # Token sin perfil ni cliente_id -> 401.
    token = crear_access_token({"sub": "x"})
    with pytest.raises(HTTPException) as exc:
        deps.get_current_cliente_o_comite(_creds(token))
    assert exc.value.status_code == 401
