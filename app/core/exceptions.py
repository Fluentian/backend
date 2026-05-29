"""Custom exception classes and FastAPI exception handlers."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


# ── Exception Hierarchy ─────────────────────────────────


class FluentianException(Exception):
    """Base exception for all Fluentian business errors."""

    status_code: int = 500

    def __init__(self, message: str, detail: Any = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(FluentianException):
    """Resource not found — 404."""

    status_code = 404


class UnauthorizedError(FluentianException):
    """Authentication failed — 401."""

    status_code = 401


class ForbiddenError(FluentianException):
    """Insufficient permissions — 403."""

    status_code = 403


class ValidationError(FluentianException):
    """Business-logic validation failure — 422."""

    status_code = 422


class ConflictError(FluentianException):
    """Duplicate / conflict — 409."""

    status_code = 409


# ── Handler Registration ───────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all custom exception handlers to the FastAPI app."""

    @app.exception_handler(FluentianException)
    async def fluentian_exception_handler(
        _request: Request, exc: FluentianException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": type(exc).__name__,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", ""),
                    "type": error.get("type", ""),
                }
            )
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "message": "Request validation failed",
                "detail": errors,
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error("Database error: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An internal error occurred. Please try again later.",
                "detail": None,
            },
        )
