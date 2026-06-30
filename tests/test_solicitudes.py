"""Tests del servicio de solicitudes (sin tocar Supabase)."""

import re
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.controllers import ctl_solicitudes
from app.repositories import rep_solicitudes
from app.schemas.sch_solicitudes import SolicitudCrearIn
from app.services import svc_solicitudes
from app.services.credito import TEA_CON_DESGRAVAMEN, TEA_SIN_DESGRAVAMEN


def test_cuota_estimada_reusa_motor():
    # Caso del motor: 1000 / sin desgravamen / 12m -> 100.95
    payload = SolicitudCrearIn(
        monto_solicitado=Decimal("1000"),
        plazo_meses=12,
        destino_credito="capital de trabajo",
        garantia="sin_garantia",
        con_desgravamen=False,
    )
    data = svc_solicitudes.preparar_solicitud("cli-123", payload)

    assert Decimal(data["cuota_estimada"]) == Decimal("100.95")
    assert Decimal(data["tea_referencial"]) == TEA_SIN_DESGRAVAMEN
    assert data["estado"] == "enviado"
    assert data["cliente_id"] == "cli-123"
    assert data["canal"] == "cliente"  # la origina el cliente; respeta el CHECK
    assert data["canal"] in svc_solicitudes.CANALES_VALIDOS
    assert "asesor_id" not in data  # decisión pendiente, no se inventa


def test_elegir_tea():
    assert svc_solicitudes.elegir_tea(True) == TEA_CON_DESGRAVAMEN
    assert svc_solicitudes.elegir_tea(False) == TEA_SIN_DESGRAVAMEN


def test_numero_expediente_formato():
    numero = svc_solicitudes.generar_numero_expediente()
    assert re.fullmatch(r"EXP-\d{8}-\d{4}", numero)


def test_estado_inicial_es_valido():
    assert svc_solicitudes.ESTADO_INICIAL in svc_solicitudes.ESTADOS_VALIDOS


def test_resolver_asesor_usa_el_del_cliente(monkeypatch):
    monkeypatch.setattr(
        rep_solicitudes, "obtener_asesor_id_de_cliente", lambda cid: "asesor-del-cliente"
    )
    assert ctl_solicitudes.resolver_asesor_id("cli-1") == "asesor-del-cliente"


def test_resolver_asesor_usa_fallback(monkeypatch):
    monkeypatch.setattr(
        rep_solicitudes, "obtener_asesor_id_de_cliente", lambda cid: None
    )
    monkeypatch.setattr(
        ctl_solicitudes,
        "get_settings",
        lambda: SimpleNamespace(ASESOR_SIN_ASIGNAR_ID="asesor-fallback"),
    )
    assert ctl_solicitudes.resolver_asesor_id("cli-1") == "asesor-fallback"


def test_resolver_asesor_sin_opciones_lanza_409(monkeypatch):
    monkeypatch.setattr(
        rep_solicitudes, "obtener_asesor_id_de_cliente", lambda cid: None
    )
    monkeypatch.setattr(
        ctl_solicitudes,
        "get_settings",
        lambda: SimpleNamespace(ASESOR_SIN_ASIGNAR_ID=None),
    )
    with pytest.raises(HTTPException) as exc:
        ctl_solicitudes.resolver_asesor_id("cli-1")
    assert exc.value.status_code == 409
