"""Cálculo del desembolso (lógica pura, sin tocar BD).

Usa el motor de cálculo ya validado (``app.services.credito``) para generar el
cronograma sobre el monto efectivamente aprobado.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.credito import Cuota, generar_cronograma


def preparar_desembolso(
    monto,
    tea: Decimal,
    plazo_meses: int,
    fecha_desembolso: date,
    dia_pago: int,
) -> dict:
    """Calcula el cronograma y resume los datos del crédito a crear.

    Returns:
        dict con ``cuota_mensual``, ``cuotas_total``, ``fecha_vencimiento`` (último
        vencimiento), ``fecha_primera_cuota``, ``fecha_ultima_cuota`` y la lista
        ``cronograma`` de objetos ``Cuota``.
    """
    cronograma: list[Cuota] = generar_cronograma(
        monto, tea, plazo_meses, fecha_desembolso, dia_pago
    )

    return {
        "cuota_mensual": cronograma[0].cuota,
        "cuotas_total": len(cronograma),
        "fecha_primera_cuota": cronograma[0].fecha_pago,
        "fecha_ultima_cuota": cronograma[-1].fecha_pago,
        "fecha_vencimiento": cronograma[-1].fecha_pago,
        "cronograma": cronograma,
    }
