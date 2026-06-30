"""Lógica de negocio para crear una solicitud de crédito.

Reusa el motor de cálculo ya validado (``app.services.credito``) para la TEA y
la cuota estimada. No toca la base de datos: solo prepara los datos a insertar.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from decimal import Decimal

from app.schemas.sch_solicitudes import SolicitudCrearIn
from app.services.credito import (
    TEA_CON_DESGRAVAMEN,
    TEA_SIN_DESGRAVAMEN,
    calcular_cuota,
)

# Estados válidos del expediente (CHECK no listado en SCHEMA.md; valores tomados
# de los 30 casos del proyecto). Usar SOLO estos literales.
ESTADOS_VALIDOS = (
    "borrador",
    "enviado",
    "recibido_comite",
    "en_evaluacion",
    "aprobado",
    "condicionado",
    "rechazado",
    "desembolsado",
)

# Cuando el cliente origina la solicitud desde su app, nace en 'enviado'.
ESTADO_INICIAL = "enviado"

# Canal de origen (CHECK del esquema: canal IN ('cliente','asesor')).
CANALES_VALIDOS = ("cliente", "asesor")
CANAL_ORIGEN_CLIENTE = "cliente"


def elegir_tea(con_desgravamen: bool) -> Decimal:
    """Devuelve la TEA aplicable según cobertura de desgravamen."""
    return TEA_CON_DESGRAVAMEN if con_desgravamen else TEA_SIN_DESGRAVAMEN


def generar_numero_expediente(momento: datetime | None = None) -> str:
    """Genera un número de expediente con formato ``EXP-YYYYMMDD-NNNN``.

    NNNN es un sufijo aleatorio de 4 dígitos. La columna ``numero_expediente`` es
    UNIQUE en el esquema; en producción conviene respaldarlo con una secuencia/
    reintento ante colisión. Aquí basta para el flujo de creación.
    """
    momento = momento or datetime.now(timezone.utc)
    sufijo = f"{random.randint(0, 9999):04d}"
    return f"EXP-{momento:%Y%m%d}-{sufijo}"


def preparar_solicitud(cliente_id: str, payload: SolicitudCrearIn) -> dict:
    """Construye el dict de inserción para ``solicitudes_credito``.

    Calcula ``tea_referencial`` y ``cuota_estimada`` con el motor validado y fija
    el estado inicial. Los valores ``Decimal`` se serializan como str para
    preservar precisión al enviarlos a PostgREST (numeric).

    NOTA: NO incluye ``asesor_id`` (columna NOT NULL en el esquema). Su resolución
    es una decisión pendiente y la añade el controller antes del insert.
    """
    tea = elegir_tea(payload.con_desgravamen)
    cuota = calcular_cuota(payload.monto_solicitado, tea, payload.plazo_meses)

    return {
        "cliente_id": cliente_id,
        "numero_expediente": generar_numero_expediente(),
        "tipo_negocio": payload.tipo_negocio,
        "nombre_negocio": payload.nombre_negocio,
        "monto_solicitado": str(payload.monto_solicitado),
        "plazo_meses": payload.plazo_meses,
        "moneda": "PEN",
        "tipo_cuota": "mensual",
        "garantia": payload.garantia,
        "destino_credito": payload.destino_credito,
        "cuota_estimada": str(cuota),
        "tea_referencial": str(tea),
        "estado": ESTADO_INICIAL,
        "paso_actual": 1,
        "pendiente_sync": False,
        "canal": CANAL_ORIGEN_CLIENTE,
    }
