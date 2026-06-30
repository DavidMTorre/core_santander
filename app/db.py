"""Cliente de Supabase (service_role) como dependencia inyectable de FastAPI.

El Core se conecta con la SERVICE_ROLE key: tiene acceso de servicio y se salta
el RLS por diseño. Nunca exponer esta key al cliente (Flutter / React).
"""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """Crea (una sola vez) y devuelve el cliente Supabase con service_role.

    Uso como dependencia:

        from fastapi import Depends
        from supabase import Client
        from app.db import get_supabase

        @router.get("/algo")
        def handler(db: Client = Depends(get_supabase)):
            ...
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
