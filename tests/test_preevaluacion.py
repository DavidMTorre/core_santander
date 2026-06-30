"""Tests de la pre-evaluación (función pura, sin tocar Supabase)."""

from decimal import Decimal

import pytest

from app.services.svc_preevaluacion import pre_evaluar


def test_caso1_apto_ratio_7_8():
    # ing 2200, gasto 900 -> disponible 1300; cuota 100.95 -> ratio ~7.8%
    r = pre_evaluar(2200, 900, Decimal("100.95"))
    assert r["veredicto"] == "APTO"
    assert r["puntaje"] == 85
    assert r["disponible"] == 1300.0
    assert r["ratio_cuota"] == pytest.approx(0.0776, abs=0.001)


def test_caso30_apto_ratio_47():
    # ing 7000, gasto 3200 -> disponible 3800; cuota 1786.83 -> ratio ~47%
    r = pre_evaluar(7000, 3200, Decimal("1786.83"))
    assert r["veredicto"] == "APTO"
    assert r["puntaje"] == 85
    assert r["ratio_cuota"] == pytest.approx(0.4702, abs=0.001)


def test_caso29_revisar_ratio_146():
    # ing 1800, gasto 1100 -> disponible 700; cuota 1024.87 -> ratio ~146%
    r = pre_evaluar(1800, 1100, Decimal("1024.87"))
    assert r["veredicto"] == "REVISAR"
    assert r["puntaje"] == 60
    assert r["ratio_cuota"] == pytest.approx(1.4641, abs=0.001)


def test_disponible_no_positivo_revisar():
    r = pre_evaluar(1000, 1000, Decimal("100"))
    assert r["veredicto"] == "REVISAR"
    assert r["puntaje"] == 60
    assert r["ratio_cuota"] is None
