"""Tests de la decisión de comité (función pura + regla de seguridad)."""

from app.controllers import ctl_comite
from app.repositories import rep_clientes, rep_solicitudes
from app.schemas.sch_comite import ResolucionComiteIn
from app.services import svc_buro
from app.services.svc_comite import (
    SUGERENCIA_APROBADO,
    SUGERENCIA_RECHAZADO,
    SUGERENCIA_REVISAR_COMITE,
    sugerir_decision,
)

APTO = {"veredicto": "APTO", "puntaje": 85}
REVISAR = {"veredicto": "REVISAR", "puntaje": 60}


def _buro(digito: int) -> dict:
    return svc_buro.consultar_buro(f"1234567{digito}")


def test_inhabilitado_digito_7_rechazado():
    s = sugerir_decision(_buro(7), APTO)
    assert s["sugerencia"] == SUGERENCIA_RECHAZADO
    assert "inhabilitados" in s["motivo"].lower()


def test_dudoso_digito_4_rechazado():
    s = sugerir_decision(_buro(4), APTO)
    assert s["sugerencia"] == SUGERENCIA_RECHAZADO
    assert "DUDOSO" in s["motivo"]


def test_normal_digito_0_apto_aprobado():
    s = sugerir_decision(_buro(0), APTO)
    assert s["sugerencia"] == SUGERENCIA_APROBADO


def test_cpp_digito_2_revisar_comite():
    s = sugerir_decision(_buro(2), APTO)
    assert s["sugerencia"] == SUGERENCIA_REVISAR_COMITE


def test_cpp_digito_8_revisar_comite():
    s = sugerir_decision(_buro(8), APTO)
    assert s["sugerencia"] == SUGERENCIA_REVISAR_COMITE


def test_normal_pero_revisar_rechazado():
    # NORMAL (díg 0) pero capacidad insuficiente -> rechazado por capacidad.
    s = sugerir_decision(_buro(0), REVISAR)
    assert s["sugerencia"] == SUGERENCIA_RECHAZADO
    assert "Capacidad" in s["motivo"]


def test_resolver_no_aprueba_inhabilitado(monkeypatch):
    capturado = {}

    def fake_obtener_por_id(solicitud_id, db=None):
        return {"id": solicitud_id, "cliente_id": "c1", "monto_solicitado": 5000}

    def fake_obtener_cliente(cliente_id, db=None):
        # Documento que termina en 7 -> buró inhabilitado.
        return {"id": cliente_id, "numero_documento": "40123457", "ingresos_estimados": 3000}

    def fake_actualizar_resolucion(solicitud_id, estado, monto_aprobado=None,
                                   motivo_rechazo=None, condicion_adicional=None, db=None):
        capturado["estado"] = estado
        capturado["motivo_rechazo"] = motivo_rechazo
        return {"id": solicitud_id, "estado": estado}

    monkeypatch.setattr(rep_solicitudes, "obtener_por_id", fake_obtener_por_id)
    monkeypatch.setattr(rep_clientes, "obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr(rep_solicitudes, "actualizar_resolucion", fake_actualizar_resolucion)

    payload = ResolucionComiteIn(decision="aprobado")
    resultado = ctl_comite.resolver_solicitud("sol-1", payload)

    assert resultado.estado == "rechazado"  # se forzó el rechazo
    assert resultado.forzado is True
    assert capturado["estado"] == "rechazado"  # lo que realmente se persistió
