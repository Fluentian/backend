"""CORS, logging, and middleware configuration."""

import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI application."""

    # ── CORS ────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request Logging ─────────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
        """Log every request with method, path, status, and duration."""
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
