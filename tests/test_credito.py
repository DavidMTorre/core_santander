"""Tests del motor de cálculo de crédito.

Casos reales validados del proyecto. Todos deben pasar.
"""

from datetime import date
from decimal import Decimal

from app.services.credito import (
    TEA_CON_DESGRAVAMEN,
    TEA_SIN_DESGRAVAMEN,
    calcular_cuota,
    generar_cronograma,
)


def test_1000_sin_desgravamen_12m():
    cuota = calcular_cuota(Decimal("1000"), TEA_SIN_DESGRAVAMEN, 12)
    assert cuota == Decimal("100.95")

    cronograma = generar_cronograma(
        Decimal("1000"), TEA_SIN_DESGRAVAMEN, 12, date(2025, 1, 15), 15
    )
    c1 = cronograma[0]
    assert c1.capital == Decimal("70.14")
    assert c1.interes == Decimal("30.81")
    assert c1.saldo == Decimal("929.86")
    assert cronograma[-1].saldo == Decimal("0.00")


def test_3000_con_desgravamen_12m():
    cuota = calcular_cuota(Decimal("3000"), TEA_CON_DESGRAVAMEN, 12)
    assert cuota == Decimal("299.59")

    cronograma = generar_cronograma(
        Decimal("3000"), TEA_CON_DESGRAVAMEN, 12, date(2025, 1, 10), 10
    )
    c1 = cronograma[0]
    assert c1.capital == Decimal("212.60")
    assert c1.interes == Decimal("86.99")
    assert c1.saldo == Decimal("2787.40")
    assert cronograma[-1].saldo == Decimal("0.00")


def test_10000_sin_desgravamen_12m():
    cuota = calcular_cuota(Decimal("10000"), TEA_SIN_DESGRAVAMEN, 12)
    assert cuota == Decimal("1009.46")


def test_20000_sin_desgravamen_36m():
    cuota = calcular_cuota(Decimal("20000"), TEA_SIN_DESGRAVAMEN, 36)
    assert cuota == Decimal("927.12")


def test_7000_con_desgravamen_18m():
    cuota = calcular_cuota(Decimal("7000"), TEA_CON_DESGRAVAMEN, 18)
    assert cuota == Decimal("504.66")


def test_8000_sin_desgravamen_6m():
    cuota = calcular_cuota(Decimal("8000"), TEA_SIN_DESGRAVAMEN, 6)
    assert cuota == Decimal("1480.73")


def test_cronograma_cierra_en_cero():
    """El saldo final debe quedar exactamente en 0.00 en varios escenarios."""
    escenarios = [
        (Decimal("1000"), TEA_SIN_DESGRAVAMEN, 12),
        (Decimal("3000"), TEA_CON_DESGRAVAMEN, 12),
        (Decimal("20000"), TEA_SIN_DESGRAVAMEN, 36),
        (Decimal("7000"), TEA_CON_DESGRAVAMEN, 18),
    ]
    for monto, tea, plazo in escenarios:
        cronograma = generar_cronograma(monto, tea, plazo, date(2025, 1, 5), 5)
        assert len(cronograma) == plazo
        assert cronograma[-1].saldo == Decimal("0.00")
