"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import setup_middleware
from app.routers import (
    analytics,
    auth,
    content,
    import_content,
    notifications,
    opportunities,
    progress,
    students,
    users,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and run startup schema checks."""

    from app.database import engine, init_db

    try:
        with open("startup_debug.txt", "w") as f:
            f.write("Startup task started\n")

        # 0. Initialize tables
        await init_db()

        with open("startup_debug.txt", "a") as f:
            f.write("init_db done\n")

        # 1. Verify and patch schema
        async with engine.begin() as conn:
            # Languages table
            await conn.execute(
                text(
                    "ALTER TABLE languages "
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE languages "
                    "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )

            # Units table
            await conn.execute(
                text(
                    "ALTER TABLE path_units "
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE path_units "
                    "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )

            # Lessons table
            await conn.execute(
                text(
                    "ALTER TABLE lessons "
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE lessons "
                    "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )

            # Blocks table
            await conn.execute(
                text(
                    "ALTER TABLE lesson_blocks "
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE lesson_blocks "
                    "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )

            # Questions table
            await conn.execute(
                text(
                    "ALTER TABLE questions "
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE questions "
                    "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"
                )
            )

            # Opportunity applications table
            await conn.execute(
                text(
                    "ALTER TABLE opportunity_applications "
                    "ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE opportunity_applications "
                    "ADD COLUMN IF NOT EXISTS email VARCHAR(255)"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE opportunity_applications "
                    "ADD COLUMN IF NOT EXISTS phone VARCHAR(50)"
                )
            )
            await conn.execute(
                text("ALTER TABLE opportunity_applications ADD COLUMN IF NOT EXISTS education TEXT")
            )
            await conn.execute(
                text(
                    "ALTER TABLE opportunity_applications ADD COLUMN IF NOT EXISTS experience TEXT"
                )
            )
            await conn.execute(
                text("ALTER TABLE opportunity_applications ADD COLUMN IF NOT EXISTS skills TEXT")
            )

            # Seed French language
            await conn.execute(
                text(
                    """
                    INSERT INTO languages (
                        id,
                        iso_code,
                        english_name,
                        native_name,
                        is_active,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        'ad9b4000-0000-4000-a000-000000000001',
                        'fr',
                        'French',
                        'Français',
                        true,
                        NOW(),
                        NOW()
                    )
                    ON CONFLICT (iso_code) DO NOTHING
                    """
                )
            )

        with open("startup_debug.txt", "a") as f:
            f.write("Seed command executed\n")

        logger.info("Database schema verified and updated.")

    except Exception as e:
        logger.error("Startup database operation failed: %s", e)

        with open("startup_debug.txt", "a") as f:
            f.write(f"FATAL ERROR: {e}\n")

    yield

    try:
        await engine.dispose()
        logger.info("Database engine disposed.")
    except Exception as e:
        logger.error("Shutdown cleanup failed: %s", e)


app = FastAPI(
    title="Fluentian API",
    version="1.0.0",
    description="AI-powered French learning platform API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Setup middleware and exception handlers
setup_middleware(app)
register_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(opportunities.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(import_content.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/")
async def api_info():
    """Root info endpoint."""
    return {
        "name": "Fluentian API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else None,
    }
