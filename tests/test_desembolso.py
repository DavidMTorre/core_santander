"""Tests del desembolso (servicio puro + selección de monto efectivo)."""

from datetime import date
from decimal import Decimal

from app.controllers import ctl_desembolso
from app.repositories import rep_creditos, rep_solicitudes
from app.services.credito import TEA_CON_DESGRAVAMEN, TEA_SIN_DESGRAVAMEN
from app.services.svc_desembolso import preparar_desembolso


def test_caso1_cronograma_12_cuotas():
    datos = preparar_desembolso(
        Decimal("1000"), TEA_SIN_DESGRAVAMEN, 12, date(2026, 2, 2), 3
    )
    assert datos["cuotas_total"] == 12
    assert datos["cuota_mensual"] == Decimal("100.95")
    # La primera cuota vence el mes siguiente al desembolso, día 3.
    assert datos["fecha_primera_cuota"] == date(2026, 3, 3)
    assert datos["fecha_ultima_cuota"] == date(2027, 2, 3)
    assert datos["cronograma"][-1].saldo == Decimal("0.00")


def test_caso25_condicionado_monto_7000():
    # Condicionado: el cronograma se calcula sobre 7000 (no sobre el solicitado).
    datos = preparar_desembolso(
        Decimal("7000"), TEA_CON_DESGRAVAMEN, 18, date(2026, 2, 2), 3
    )
    assert datos["cuotas_total"] == 18
    assert datos["cuota_mensual"] == Decimal("504.66")


def test_desembolso_condicionado_usa_monto_aprobado(monkeypatch):
    capturado = {}

    def fake_obtener_por_id(solicitud_id, db=None):
        return {
            "id": solicitud_id,
            "cliente_id": "c1",
            "asesor_id": "a1",
            "agencia_id": None,
            "estado": "condicionado",
            "monto_solicitado": 11000,   # NO debe usarse
            "monto_aprobado": 7000,      # SÍ debe usarse
            "plazo_meses": 18,
            "tea_referencial": str(TEA_CON_DESGRAVAMEN),
            "garantia": "sin_garantia",
        }

    def fake_crear_credito(data, db=None):
        capturado["credito_data"] = data
        return {"id": "cred-1", **data}

    def fake_crear_cuotas(credito_id, cliente_id, cuotas, db=None):
        capturado["num_cuotas"] = len(list(cuotas))
        capturado["cliente_id_cuotas"] = cliente_id
        return []

    def fake_actualizar_estado(solicitud_id, estado, db=None):
        capturado["estado_solicitud"] = estado
        return {"id": solicitud_id, "estado": estado}

    monkeypatch.setattr(rep_solicitudes, "obtener_por_id", fake_obtener_por_id)
    monkeypatch.setattr(rep_creditos, "crear_credito", fake_crear_credito)
    monkeypatch.setattr(rep_creditos, "crear_cuotas_cronograma", fake_crear_cuotas)
    monkeypatch.setattr(rep_solicitudes, "actualizar_estado", fake_actualizar_estado)

    out = ctl_desembolso.desembolsar_solicitud("sol-1", date(2026, 2, 2), 3)

    assert out.monto_desembolsado == Decimal("7000")
    assert out.cuota_mensual == Decimal("504.66")
    assert out.cuotas_total == 18
    assert capturado["credito_data"]["monto_desembolsado"] == "7000"
    assert capturado["credito_data"]["saldo_actual"] == "7000"
    assert capturado["num_cuotas"] == 18
    assert capturado["cliente_id_cuotas"] == "c1"
    assert capturado["estado_solicitud"] == "desembolsado"


def test_desembolso_rechaza_solicitud_no_aprobada(monkeypatch):
    import pytest
    from fastapi import HTTPException

    monkeypatch.setattr(
        rep_solicitudes,
        "obtener_por_id",
        lambda solicitud_id, db=None: {"id": solicitud_id, "estado": "enviado"},
    )
    with pytest.raises(HTTPException) as exc:
        ctl_desembolso.desembolsar_solicitud("sol-x", date(2026, 2, 2), 3)
    assert exc.value.status_code == 409
