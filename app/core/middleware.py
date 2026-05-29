"""CORS, logging, and middleware configuration."""

import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.config import settings

from starlette.types import ASGIApp, Receive, Scope, Send, Message

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """ASGI middleware to log every request with method, path, status, and duration."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = [500]

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s → %d (%.1fms)",
                scope["method"],
                scope["path"],
                status_code[0],
                duration_ms,
            )


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
    app.add_middleware(RequestLoggingMiddleware)

