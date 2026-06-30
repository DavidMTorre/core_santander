"""Sugerencia automática de decisión de comité (función pura).

Combina el resultado del buró con la pre-evaluación de capacidad de pago para
producir una SUGERENCIA (no la resolución final, que la registra el comité).
Reglas derivadas de los 30 casos del proyecto.
"""

from __future__ import annotations

SUGERENCIA_RECHAZADO = "RECHAZADO"
SUGERENCIA_APROBADO = "APROBADO"
SUGERENCIA_REVISAR_COMITE = "REVISAR_COMITE"

_CALIF_NO_APTAS = ("DUDOSO", "PERDIDA")
_CALIF_REVISAR = ("CPP", "DEFICIENTE")


def sugerir_decision(buro: dict, preevaluacion: dict) -> dict:
    """Sugiere una decisión a partir del buró y la pre-evaluación.

    Returns:
        dict con: ``sugerencia`` (RECHAZADO|APROBADO|REVISAR_COMITE),
        ``motivo`` (str) y ``monto_sugerido`` (None aquí; el controller lo
        completa con el monto solicitado cuando la sugerencia es APROBADO).
    """
    calificacion = buro.get("calificacion_sbs")
    inhabilitado = bool(buro.get("inhabilitado"))
    veredicto = preevaluacion.get("veredicto")

    # 1) Inhabilitado: rechazo inmediato (caso 28).
    if inhabilitado:
        return {
            "sugerencia": SUGERENCIA_RECHAZADO,
            "motivo": "En lista de inhabilitados del sistema financiero",
            "monto_sugerido": None,
        }

    # 2) Calificación SBS no apta (casos 29, 30).
    if calificacion in _CALIF_NO_APTAS:
        return {
            "sugerencia": SUGERENCIA_RECHAZADO,
            "motivo": f"Calificación SBS no apta ({calificacion}) con mora vigente",
            "monto_sugerido": None,
        }

    # 3) Capacidad de pago insuficiente (caso 29).
    if veredicto == "REVISAR":
        return {
            "sugerencia": SUGERENCIA_RECHAZADO,
            "motivo": "Capacidad de pago insuficiente",
            "monto_sugerido": None,
        }

    # 4) NORMAL + pre-evaluación APTA -> aprobar al monto solicitado (casos 1-13).
    if calificacion == "NORMAL" and veredicto == "APTO":
        return {
            "sugerencia": SUGERENCIA_APROBADO,
            "motivo": "Buró NORMAL y capacidad de pago suficiente",
            "monto_sugerido": None,  # el controller lo fija al monto solicitado
        }

    # 5) CPP / DEFICIENTE -> requiere decisión humana de monto (casos 14, 16, 25-27).
    if calificacion in _CALIF_REVISAR:
        return {
            "sugerencia": SUGERENCIA_REVISAR_COMITE,
            "motivo": f"Calificación {calificacion}: requiere decisión de comité sobre el monto",
            "monto_sugerido": None,
        }

    # Fallback conservador: ante cualquier combinación no contemplada, a comité.
    return {
        "sugerencia": SUGERENCIA_REVISAR_COMITE,
        "motivo": "Caso no concluyente: requiere decisión de comité",
        "monto_sugerido": None,
    }
