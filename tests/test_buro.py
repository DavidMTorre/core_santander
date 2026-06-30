"""Tests del buró simulado (función pura, sin tocar Supabase)."""

import pytest

from app.services.svc_buro import consultar_buro

# Perfil esperado por último dígito: (calificacion, entidades, deuda, dias_mora, inhabilitado).
PERFILES_ESPERADOS = {
    0: ("NORMAL", 1, 4500, 0, False),
    1: ("NORMAL", 2, 12000, 0, False),
    2: ("CPP", 2, 18000, 15, False),
    3: ("NORMAL", 0, 0, 0, False),
    4: ("DUDOSO", 3, 25000, 95, False),
    5: ("DEFICIENTE", 2, 16000, 45, False),
    6: ("NORMAL", 1, 6000, 0, False),
    7: ("PERDIDA", 4, 40000, 210, True),
    8: ("CPP", 1, 9000, 20, False),
    9: ("NORMAL", 2, 14000, 0, False),
}


@pytest.mark.parametrize("digito,esperado", PERFILES_ESPERADOS.items())
def test_buro_por_digito(digito, esperado):
    calificacion, entidades, deuda, dias, inhabilitado = esperado
    # Documento que termina en el dígito a probar.
    resultado = consultar_buro(f"1234567{digito}")

    assert resultado["calificacion_sbs"] == calificacion
    assert resultado["entidades_con_deuda"] == entidades
    assert resultado["deuda_total_pen"] == deuda
    assert resultado["mayor_deuda"] == deuda  # mismo valor que deuda_total por ahora
    assert resultado["dias_mayor_mora"] == dias
    assert resultado["inhabilitado"] is inhabilitado


def test_buro_digito_0_caso_explicito():
    r = consultar_buro("40123450")
    assert (r["calificacion_sbs"], r["entidades_con_deuda"], r["deuda_total_pen"], r["dias_mayor_mora"]) == (
        "NORMAL",
        1,
        4500,
        0,
    )


def test_buro_digito_7_inhabilitado():
    r = consultar_buro("40123457")
    assert r["calificacion_sbs"] == "PERDIDA"
    assert r["entidades_con_deuda"] == 4
    assert r["deuda_total_pen"] == 40000
    assert r["dias_mayor_mora"] == 210
    assert r["inhabilitado"] is True


def test_buro_digito_4():
    r = consultar_buro("40123454")
    assert (r["calificacion_sbs"], r["entidades_con_deuda"], r["deuda_total_pen"], r["dias_mayor_mora"]) == (
        "DUDOSO",
        3,
        25000,
        95,
    )


def test_buro_documento_vacio():
    with pytest.raises(ValueError):
        consultar_buro("")


def test_buro_documento_no_numerico():
    with pytest.raises(ValueError):
        consultar_buro("ABCDE")
