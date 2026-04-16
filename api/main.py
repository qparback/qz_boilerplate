"""
FastAPI application factory.

Layout:
    /health   public, no auth
    /admin/*  Jinja-based admin UI (Caddy IP-restricts in prod)
    /api/v1/* protected endpoints (require x-api-key header)

The whole app is mounted behind Caddy's `handle_path /api/*`, which strips
the `/api` prefix before forwarding. `root_path="/api"` here only affects
how OpenAPI documents the URLs (so Swagger shows /api/...).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.openapi.utils import get_openapi

from admin.router import router as admin_router
from api.config import settings
from api.exceptions import register_exception_handlers
from api.middleware import RequestIDMiddleware
from api.security import verify_api_key


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.project_name, settings.app_env)
    yield
    logger.info("Shutting down %s", settings.project_name)


app = FastAPI(
    title=f"{settings.project_name} API",
    version="0.1.0",
    root_path="/api",
    swagger_ui_parameters={"displayRequestDuration": True},
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)


# ─── Public routes ────────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


# ─── Protected routes ─────────────────────────────────────────────────────────
# Add resource routers here. Example:
#   from api.routers.users import router as users_router
#   app.include_router(users_router, prefix="/v1", dependencies=[Depends(verify_api_key)])

# Sentinel route used by integration tests to verify auth enforcement.
@app.get("/v1/_auth_check", dependencies=[Depends(verify_api_key)], include_in_schema=False)
async def auth_check() -> dict:
    return {"ok": True}


# ─── Admin UI ─────────────────────────────────────────────────────────────────
# Mounted on the same app so Caddy can route /admin/* directly to FastAPI.
app.include_router(admin_router)


# ─── OpenAPI customization ────────────────────────────────────────────────────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {"type": "apiKey", "in": "header", "name": "x-api-key"}
    }
    schema["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
