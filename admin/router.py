"""
Admin web interface — mounted on the FastAPI app at /admin.

Auth model: in production, Caddy IP-restricts /admin/* before the request
ever reaches FastAPI. In dev, the interface is open. Do NOT add API key
checks here — the Caddy IP whitelist is the boundary.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(ADMIN_DIR / "templates"))

# Static files mounted on the router so /admin/static/* resolves cleanly.
router.mount(
    "/static",
    StaticFiles(directory=str(ADMIN_DIR / "static")),
    name="admin-static",
)


def _common_context(request: Request) -> dict:
    return {
        "request": request,
        "project_name": settings.project_name,
        "app_env": settings.app_env,
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "error"

    recent_errors = (
        await db.execute(
            text(
                """
                SELECT service, operation, message, created_at
                FROM app_logs
                WHERE level IN ('ERROR','CRITICAL')
                ORDER BY created_at DESC
                LIMIT 10
                """
            )
        )
    ).fetchall()

    email_stats = {
        row.status: row.count
        for row in (
            await db.execute(
                text(
                    """
                    SELECT status, COUNT(*) AS count
                    FROM email_log
                    WHERE sent_at > NOW() - INTERVAL '24 hours'
                    GROUP BY status
                    """
                )
            )
        ).fetchall()
    }

    prompt_count = (
        await db.execute(text("SELECT COUNT(*) AS c FROM prompts WHERE active = TRUE"))
    ).scalar()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            **_common_context(request),
            "db_status": db_status,
            "recent_errors": recent_errors,
            "email_stats": email_stats,
            "prompt_count": prompt_count,
        },
    )


@router.get("/logs", response_class=HTMLResponse)
async def logs(
    request: Request,
    level: str | None = None,
    service: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = "SELECT * FROM app_logs WHERE 1=1"
    params: dict = {}
    if level:
        query += " AND level = :level"
        params["level"] = level
    if service:
        query += " AND service = :service"
        params["service"] = service
    query += " ORDER BY created_at DESC LIMIT 200"

    rows = (await db.execute(text(query), params)).fetchall()
    return templates.TemplateResponse(
        request,
        "logs.html",
        {
            **_common_context(request),
            "logs": rows,
            "filter_level": level,
            "filter_service": service,
        },
    )


@router.get("/prompts", response_class=HTMLResponse)
async def prompts(request: Request, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text("SELECT * FROM prompts ORDER BY key"))).fetchall()
    return templates.TemplateResponse(
        request,
        "prompts.html",
        {**_common_context(request), "prompts": rows},
    )


@router.get("/roadmap", response_class=HTMLResponse)
async def roadmap(request: Request, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(text("SELECT * FROM roadmap_items ORDER BY phase, priority"))
    ).fetchall()
    return templates.TemplateResponse(
        request,
        "roadmap.html",
        {**_common_context(request), "items": rows},
    )
