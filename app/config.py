"""Configuración centralizada cargada desde variables de entorno (.env)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de la aplicación. Se leen de .env (no se hardcodean)."""

    # Supabase (el Core usa la service_role key: se salta el RLS por diseño).
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # JWT (auth se implementará más adelante; aquí solo se configura).
    JWT_SECRET: str = "cambiar-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Servidor. En producción (Koyeb) el puerto lo asigna la plataforma vía $PORT;
    # en local se usa 8003 como fallback.
    PORT: int = 8003

    # CORS: lista de orígenes permitidos separados por comas. Default = dev (Vite).
    # En producción agregar aquí la URL del frontend (p. ej. el dominio de Vercel).
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Asesor por defecto cuando el cliente origina una solicitud y aún no tiene
    # asesor asignado (asesor_id es NOT NULL en solicitudes_credito). Debe ser el
    # UUID de una fila real en asesores_negocio (ver seed "SIN_ASIGNAR").
    ASESOR_SIN_ASIGNAR_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Convierte ALLOWED_ORIGINS (CSV) en lista, ignorando espacios/vacíos."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia única de Settings (cacheada)."""
    return Settings()
