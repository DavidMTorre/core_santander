"""Configuración de entorno para los tests (variables dummy de .env).

Permite cargar ``app.config.Settings`` sin un .env real durante los tests.
"""

import os

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("JWT_SECRET", "test-secret-no-usar-en-produccion")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
