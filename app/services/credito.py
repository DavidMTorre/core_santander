"""Motor de cálculo de crédito (amortización francesa).

Lógica validada contra los 30 casos reales del proyecto. No modificar las
fórmulas ni el redondeo sin volver a validar contra esos casos.

Convenciones:
- Todo el cálculo monetario se hace en ``Decimal``.
- Las tasas son TEA (tasa efectiva anual) y se convierten a TEM (tasa efectiva
  mensual) con ``tem_desde_tea``.
- Los montos se redondean a 2 decimales con ``ROUND_HALF_UP``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta

# TEA según cobertura de desgravamen.
TEA_CON_DESGRAVAMEN = Decimal("0.4092")
TEA_SIN_DESGRAVAMEN = Decimal("0.4392")

_DOS_DECIMALES = Decimal("0.01")


def _a_decimal(valor) -> Decimal:
    """Convierte int/str/Decimal a Decimal de forma segura (evita floats)."""
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def _redondear(valor: Decimal) -> Decimal:
    """Redondea a 2 decimales con ROUND_HALF_UP."""
    return valor.quantize(_DOS_DECIMALES, rounding=ROUND_HALF_UP)


def tem_desde_tea(tea: Decimal) -> Decimal:
    """Tasa efectiva mensual a partir de la TEA: (1+TEA)^(1/12) - 1."""
    tea = _a_decimal(tea)
    return (Decimal(1) + tea) ** (Decimal(1) / Decimal(12)) - Decimal(1)


def calcular_cuota(monto, tea: Decimal, plazo_meses: int) -> Decimal:
    """Cuota fija mensual (amortización francesa), redondeada a 2 decimales.

    cuota = monto * (i * (1+i)^n) / ((1+i)^n - 1)
    donde i = TEM y n = plazo en meses.
    """
    monto = _a_decimal(monto)
    i = tem_desde_tea(tea)
    factor = (Decimal(1) + i) ** plazo_meses
    cuota = monto * (i * factor) / (factor - Decimal(1))
    return _redondear(cuota)


@dataclass
class Cuota:
    """Una fila del cronograma de pagos."""

    numero: int
    fecha_pago: date
    cuota: Decimal
    capital: Decimal
    interes: Decimal
    saldo: Decimal


def generar_cronograma(
    monto,
    tea: Decimal,
    plazo_meses: int,
    fecha_desembolso: date,
    dia_pago: int,
) -> list[Cuota]:
    """Genera el cronograma de cuotas con amortización francesa.

    - La primera cuota vence el mes siguiente al desembolso, en el día ``dia_pago``.
    - Cada mes: interés = round(saldo * TEM); capital = cuota_fija - interés.
    - La última cuota muestra la cuota fija, pero su capital es el saldo restante
      para cerrar el saldo en 0.00 (absorbe los redondeos acumulados).
    """
    monto = _a_decimal(monto)
    tem = tem_desde_tea(tea)
    cuota_fija = calcular_cuota(monto, tea, plazo_meses)

    cronograma: list[Cuota] = []
    saldo = monto

    for numero in range(1, plazo_meses + 1):
        fecha_pago = fecha_desembolso + relativedelta(months=numero, day=dia_pago)
        interes = _redondear(saldo * tem)

        if numero == plazo_meses:
            capital = saldo
            saldo = Decimal("0.00")
        else:
            capital = cuota_fija - interes
            saldo = saldo - capital

        cronograma.append(
            Cuota(
                numero=numero,
                fecha_pago=fecha_pago,
                cuota=cuota_fija,
                capital=capital,
                interes=interes,
                saldo=saldo,
            )
        )

    return cronograma
