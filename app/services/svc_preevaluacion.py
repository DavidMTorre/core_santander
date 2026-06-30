"""Pre-evaluación crediticia por capacidad de pago (función pura).

Reglas derivadas de los 30 casos del proyecto:

- disponible = ingreso - gasto
- ratio_cuota = cuota_estimada / disponible
- ratio_cuota > 1.0  -> REVISAR (puntaje 60)  [la cuota supera el disponible]
- ratio_cuota <= 1.0 -> APTO    (puntaje 85)  [la cuota cabe en el disponible]

El umbral de holgura (0.50) se conserva como referencia, pero no baja el veredicto
de APTO mientras la cuota no supere el disponible (>1.0). En los 30 casos solo el
caso con cuota al 146% del disponible salió REVISAR; el resto, APTO.
"""

from __future__ import annotations

from decimal import Decimal

VEREDICTO_APTO = "APTO"
VEREDICTO_REVISAR = "REVISAR"
VEREDICTO_NO_PROCEDE = "NO_PROCEDE"  # reservado para el comité, no se usa aquí

PUNTAJE_APTO = 85
PUNTAJE_REVISAR = 60

UMBRAL_HOLGURA = Decimal("0.50")  # referencia de holgura
UMBRAL_NO_PAGA = Decimal("1.0")   # por encima de esto, la cuota no cabe


def _a_decimal(valor) -> Decimal:
    """Convierte int/float/str/Decimal/None a Decimal (None -> 0)."""
    if valor is None:
        return Decimal(0)
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def pre_evaluar(ingreso, gasto, cuota_estimada) -> dict:
    """Evalúa la capacidad de pago y devuelve el veredicto.

    Returns:
        dict con: ``veredicto``, ``puntaje``, ``disponible``, ``ratio_cuota``.
        ``ratio_cuota`` es None cuando el disponible es <= 0 (no se puede calcular).
    """
    ingreso = _a_decimal(ingreso)
    gasto = _a_decimal(gasto)
    cuota = _a_decimal(cuota_estimada)

    disponible = ingreso - gasto

    if disponible <= 0:
        # Sin disponible no hay capacidad de pago: requiere revisión.
        return {
            "veredicto": VEREDICTO_REVISAR,
            "puntaje": PUNTAJE_REVISAR,
            "disponible": float(disponible),
            "ratio_cuota": None,
        }

    ratio = (cuota / disponible).quantize(Decimal("0.0001"))

    if ratio > UMBRAL_NO_PAGA:
        veredicto, puntaje = VEREDICTO_REVISAR, PUNTAJE_REVISAR
    else:
        veredicto, puntaje = VEREDICTO_APTO, PUNTAJE_APTO

    return {
        "veredicto": veredicto,
        "puntaje": puntaje,
        "disponible": float(disponible),
        "ratio_cuota": float(ratio),
    }
