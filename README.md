# Core Financiero — Santander

API REST (FastAPI) del Core de microfinanzas. Se conecta a Supabase (PostgreSQL)
con la `service_role` key y expone el flujo de crédito: autenticación de clientes y
comité, solicitudes, buró simulado, pre-evaluación, decisión de comité y desembolso.

## Requisitos

- Python 3.12
- Una base Supabase con el esquema de `SCHEMA.md`

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

| Variable | Obligatoria | Descripción |
|---|---|---|
| `SUPABASE_URL` | Sí | URL del proyecto Supabase |
| `SUPABASE_SERVICE_KEY` | Sí | Service-role key (se salta RLS) |
| `JWT_SECRET` | Sí (prod) | Secreto para firmar los JWT |
| `ALGORITHM` | No | Algoritmo JWT (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Expiración del token (default `60`) |
| `PORT` | No | Puerto local (default `8003`). En Koyeb lo inyecta la plataforma |
| `ALLOWED_ORIGINS` | No | Orígenes CORS separados por comas (default dev Vite) |
| `ASESOR_SIN_ASIGNAR_ID` | No | UUID de asesor fallback para solicitudes sin asesor |

## Correr en local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

- API: http://localhost:8003
- Docs (Swagger): http://localhost:8003/docs
- Healthcheck: http://localhost:8003/health

## Tests

```bash
pytest -q
```

## Producción (Koyeb)

El arranque usa `$PORT` (asignado por Koyeb). El `Procfile` define el proceso web:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- `runtime.txt` fija la versión de Python (`python-3.12`).
- `requirements.txt` tiene todas las dependencias con versiones fijadas.

Configura en Koyeb las variables: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`,
`JWT_SECRET`, `ALLOWED_ORIGINS` (incluye el dominio del frontend) y, si aplica,
`ASESOR_SIN_ASIGNAR_ID`. No definas `PORT`: Koyeb lo gestiona automáticamente.
Healthcheck recomendado: `GET /health`.
