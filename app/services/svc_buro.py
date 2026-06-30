"""Buró crediticio simulado (determinista).

La calificación depende del ÚLTIMO dígito del número de documento del cliente.
Fuente de verdad derivada de los 30 casos del proyecto. No modificar la tabla
sin volver a validar contra esos casos.
"""

from __future__ import annotations

# Perfil de buró por último dígito del documento.
# Campos: calificacion_sbs, entidades_con_deuda, deuda_total_pen, dias_mayor_mora, inhabilitado.
TABLA_BURO: dict[int, dict] = {
    0: {"calificacion_sbs": "NORMAL", "entidades_con_deuda": 1, "deuda_total_pen": 4500, "dias_mayor_mora": 0, "inhabilitado": False},
    1: {"calificacion_sbs": "NORMAL", "entidades_con_deuda": 2, "deuda_total_pen": 12000, "dias_mayor_mora": 0, "inhabilitado": False},
    2: {"calificacion_sbs": "CPP", "entidades_con_deuda": 2, "deuda_total_pen": 18000, "dias_mayor_mora": 15, "inhabilitado": False},
    3: {"calificacion_sbs": "NORMAL", "entidades_con_deuda": 0, "deuda_total_pen": 0, "dias_mayor_mora": 0, "inhabilitado": False},
    4: {"calificacion_sbs": "DUDOSO", "entidades_con_deuda": 3, "deuda_total_pen": 25000, "dias_mayor_mora": 95, "inhabilitado": False},
    5: {"calificacion_sbs": "DEFICIENTE", "entidades_con_deuda": 2, "deuda_total_pen": 16000, "dias_mayor_mora": 45, "inhabilitado": False},
    6: {"calificacion_sbs": "NORMAL", "entidades_con_deuda": 1, "deuda_total_pen": 6000, "dias_mayor_mora": 0, "inhabilitado": False},
    7: {"calificacion_sbs": "PERDIDA", "entidades_con_deuda": 4, "deuda_total_pen": 40000, "dias_mayor_mora": 210, "inhabilitado": True},
    8: {"calificacion_sbs": "CPP", "entidades_con_deuda": 1, "deuda_total_pen": 9000, "dias_mayor_mora": 20, "inhabilitado": False},
    9: {"calificacion_sbs": "NORMAL", "entidades_con_deuda": 2, "deuda_total_pen": 14000, "dias_mayor_mora": 0, "inhabilitado": False},
}


def consultar_buro(numero_documento: str) -> dict:
    """Devuelve el perfil de buró según el último dígito del documento.

    Lanza ``ValueError`` si el documento es vacío o no termina en dígito numérico.
    El campo ``mayor_deuda`` usa el mismo valor que ``deuda_total_pen`` por ahora.
    """
    if not numero_documento or not numero_documento.strip():
        raise ValueError("El número de documento está vacío.")

    documento = numero_documento.strip()
    ultimo = documento[-1]
    if not ultimo.isdigit():
        raise ValueError(
            f"El número de documento '{documento}' no termina en un dígito numérico."
        )

    perfil = TABLA_BURO[int(ultimo)]
    return {
        "calificacion_sbs": perfil["calificacion_sbs"],
        "entidades_con_deuda": perfil["entidades_con_deuda"],
        "deuda_total_pen": perfil["deuda_total_pen"],
        "mayor_deuda": perfil["deuda_total_pen"],
        "dias_mayor_mora": perfil["dias_mayor_mora"],
        "inhabilitado": perfil["inhabilitado"],
    }
