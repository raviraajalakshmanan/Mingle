"""MigleUp FastAPI application entrypoint.

M0: app wiring, CORS, structured logging, and a health route. Feature routers
(catchups, invite, results) are added from M1 onward.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.catchups import router as catchups_router
from app.api.invite import router as invite_router
from app.api.results import router as results_router
from app.core.config import get_settings
from app.core.db import is_configured
from app.core.logging import configure_logging

configure_logging()

settings = get_settings()

app = FastAPI(title=settings.app_name, version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(catchups_router)
app.include_router(invite_router)
app.include_router(results_router)


@app.get("/api/health")
def health() -> dict:
    """Liveness + configuration probe. Reports no secrets."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "supabase_configured": is_configured(),
    }
