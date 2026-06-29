"""FastAPI application entry point."""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import setup_middleware
from app.routers import (
    admin,
    ai,
    analytics,
    auth,
    content,
    import_content,
    learning,
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
            await conn.execute(
                text(
                    "ALTER TABLE questions "
                    "ADD COLUMN IF NOT EXISTS difficulty INTEGER DEFAULT 1 NOT NULL"
                )
            )

            # Spaced repetition table
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS spaced_repetition_items (
                        id UUID PRIMARY KEY,
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                        interval_days INTEGER DEFAULT 1 NOT NULL,
                        easiness_factor DOUBLE PRECISION DEFAULT 2.5 NOT NULL,
                        next_review_date TIMESTAMPTZ NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                        updated_at TIMESTAMPTZ
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_spaced_repetition_items_user_id "
                    "ON spaced_repetition_items(user_id)"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_spaced_repetition_items_question_id "
                    "ON spaced_repetition_items(question_id)"
                )
            )
            await conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS "
                    "uq_spaced_repetition_items_user_question "
                    "ON spaced_repetition_items(user_id, question_id)"
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
                text(
                    "ALTER TABLE opportunity_applications ADD COLUMN IF NOT EXISTS education TEXT"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE opportunity_applications ADD COLUMN IF NOT EXISTS experience TEXT"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE opportunity_applications ADD COLUMN IF NOT EXISTS skills TEXT"
                )
            )

            # Users table
            await conn.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE NOT NULL"
                )
            )

            # User settings table
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS learning_reminder_enabled "
                    "BOOLEAN DEFAULT TRUE NOT NULL"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS reminder_time VARCHAR(5) DEFAULT '08:00' NOT NULL"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS phonetic_hints_enabled "
                    "BOOLEAN DEFAULT TRUE NOT NULL"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS speaking_exercises_enabled "
                    "BOOLEAN DEFAULT TRUE NOT NULL"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS high_contrast_enabled "
                    "BOOLEAN DEFAULT FALSE NOT NULL"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS reduce_animations_enabled "
                    "BOOLEAN DEFAULT FALSE NOT NULL"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS haptic_feedback_enabled "
                    "BOOLEAN DEFAULT TRUE NOT NULL"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS tts_speed DOUBLE PRECISION DEFAULT 1.0 NOT NULL"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_settings "
                    "ADD COLUMN IF NOT EXISTS font_scale INTEGER DEFAULT 1 NOT NULL"
                )
            )

            # Seed French language
            await conn.execute(text("""
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
                    """))

            culture_stories = [
                {
                    "id": "ad9b4100-0000-4000-a000-000000000001",
                    "title": "La vie au café",
                    "location": "Paris, France",
                    "category": "Daily culture",
                    "sequence_no": 1,
                    "media": [
                        {
                            "type": "image",
                            "url": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&q=80&w=1200",
                            "caption": "Une terrasse parisienne",
                        },
                        {
                            "type": "image",
                            "url": "https://images.unsplash.com/photo-1522093007474-d86e9bf7ba6f?auto=format&fit=crop&q=80&w=1200",
                            "caption": "Un moment de discussion",
                        },
                    ],
                    "paragraphs": [
                        [
                            {
                                "original": "Les cafés parisiens sont au cœur de la vie sociale en France.",
                                "translated": "Parisian cafes are at the heart of social life in France.",
                            },
                            {
                                "original": "On s’y assoit en terrasse pour regarder les passants, boire un expresso et discuter pendant des heures.",
                                "translated": "People sit on the terrace to watch passers-by, drink an espresso, and talk for hours.",
                            },
                        ],
                        [
                            {
                                "original": "Historiquement, les cafés étaient des lieux de rencontre pour les artistes, les écrivains et les philosophes.",
                                "translated": "Historically, cafes were meeting places for artists, writers, and philosophers.",
                            },
                            {
                                "original": "Aujourd’hui encore, commander un café peut être une petite pause, mais aussi un rituel quotidien.",
                                "translated": "Even today, ordering a coffee can be a short break, but also a daily ritual.",
                            },
                        ],
                    ],
                },
                {
                    "id": "ad9b4100-0000-4000-a000-000000000002",
                    "title": "La Fête de la Musique",
                    "location": "Toute la France",
                    "category": "Festival",
                    "sequence_no": 2,
                    "media": [
                        {
                            "type": "image",
                            "url": "https://images.unsplash.com/photo-1508973379184-7517410fb0bc?auto=format&fit=crop&q=80&w=1200",
                            "caption": "Un concert en plein air",
                        },
                        {
                            "type": "video",
                            "url": "https://flutter.github.io/assets-for-api-docs/assets/videos/bee.mp4",
                            "caption": "Vidéo culturelle",
                        },
                    ],
                    "paragraphs": [
                        [
                            {
                                "original": "La Fête de la Musique a lieu chaque année le 21 juin, le jour du solstice d’été.",
                                "translated": "The Music Festival takes place every year on June 21, the day of the summer solstice.",
                            },
                            {
                                "original": "Des musiciens amateurs et professionnels jouent dans les rues, les parcs, les cafés et les places publiques.",
                                "translated": "Amateur and professional musicians play in streets, parks, cafes, and public squares.",
                            },
                        ],
                        [
                            {
                                "original": "L’idée principale est simple : la musique doit être accessible à tout le monde.",
                                "translated": "The main idea is simple: music should be accessible to everyone.",
                            },
                            {
                                "original": "Dans beaucoup de villes, les habitants se promènent d’un concert à l’autre jusqu’à tard le soir.",
                                "translated": "In many cities, residents walk from one concert to another until late at night.",
                            },
                        ],
                    ],
                },
                {
                    "id": "ad9b4100-0000-4000-a000-000000000003",
                    "title": "Les marchés de Provence",
                    "location": "Provence, France",
                    "category": "Food and place",
                    "sequence_no": 3,
                    "media": [
                        {
                            "type": "image",
                            "url": "https://images.unsplash.com/photo-1471194402529-8e0f5a675de6?auto=format&fit=crop&q=80&w=1200",
                            "caption": "Un marché du matin",
                        },
                        {
                            "type": "image",
                            "url": "https://images.unsplash.com/photo-1509474520651-53cf6a80536f?auto=format&fit=crop&q=80&w=1200",
                            "caption": "Produits locaux",
                        },
                    ],
                    "paragraphs": [
                        [
                            {
                                "original": "En Provence, le marché est souvent un rendez-vous de la semaine.",
                                "translated": "In Provence, the market is often a weekly meeting point.",
                            },
                            {
                                "original": "On y achète des olives, du fromage, des fruits, des herbes et parfois de la lavande.",
                                "translated": "People buy olives, cheese, fruit, herbs, and sometimes lavender there.",
                            },
                        ],
                        [
                            {
                                "original": "Les vendeurs aiment expliquer l’origine de leurs produits et proposer une dégustation.",
                                "translated": "Vendors like to explain where their products come from and offer a tasting.",
                            },
                            {
                                "original": "Pour beaucoup de visiteurs, c’est une façon naturelle de découvrir les accents, les saveurs et les habitudes locales.",
                                "translated": "For many visitors, it is a natural way to discover local accents, flavors, and habits.",
                            },
                        ],
                    ],
                },
            ]
            for story in culture_stories:
                await conn.execute(
                    text(
                        """
                        INSERT INTO culture_stories (
                            id, title, location, category, sequence_no, is_published,
                            media, paragraphs, created_at, updated_at
                        )
                        VALUES (
                            :id, :title, :location, :category, :sequence_no, true,
                            CAST(:media AS JSONB), CAST(:paragraphs AS JSONB), NOW(), NOW()
                        )
                        ON CONFLICT (id) DO NOTHING
                        """
                    ),
                    {
                        **story,
                        "media": json.dumps(story["media"]),
                        "paragraphs": json.dumps(story["paragraphs"]),
                    },
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
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(opportunities.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(import_content.router, prefix="/api/v1")
app.include_router(learning.router, prefix="/api/v1")


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
