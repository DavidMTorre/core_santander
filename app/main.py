"""Punto de entrada de la API REST del Core Financiero — Santander."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import (
    rtr_auth,
    rtr_buro,
    rtr_comite,
    rtr_desembolso,
    rtr_preevaluacion,
    rtr_solicitudes,
)

app = FastAPI(
    title="Core Financiero — Santander",
    description="API REST del Core de microfinanzas (Banco Santander - Perú).",
    version="0.1.0",
)

# CORS configurable por entorno (ALLOWED_ORIGINS). Default = dev (Vite). En
# producción se agregan los dominios reales sin tocar código.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Healthcheck simple."""
    return {"status": "ok"}


# Routers de dominio.
app.include_router(rtr_auth.router)
app.include_router(rtr_solicitudes.router)
app.include_router(rtr_buro.router)
app.include_router(rtr_preevaluacion.router)
app.include_router(rtr_comite.router)
app.include_router(rtr_desembolso.router)
