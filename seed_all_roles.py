import asyncio
import os
from urllib.parse import urlparse

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import hash_password
from app.database import AsyncSessionLocal, engine
from app.models.user import AppRole, User, UserProfile, UserSettings


async def create_database_if_not_exists():
    # Parse DATABASE_URL from .env to extract credentials
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/fluentian",
    )
    parsed = urlparse(database_url)

    # Construct admin URL to postgres default database
    admin_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"
    temp_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")

    async with temp_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname='fluentian'")
        )
        if not result.scalar():
            print("Creating database 'fluentian'...")
            await conn.execute(text("CREATE DATABASE fluentian"))
        else:
            print("Database 'fluentian' already exists.")

    await temp_engine.dispose()


async def seed_all_roles():
    """Seeds users with all roles: super_admin, admin, teacher, moderator, and student."""
    # Ensure tables are created
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Define users to seed
        users_to_create = [
            {
                "username": "superadmin",
                "email": "superadmin@fluentian.com",
                "role": AppRole.super_admin,
                "display_name": "Super Administrator",
            },
            {
                "username": "admin",
                "email": "admin@fluentian.com",
                "role": AppRole.admin,
                "display_name": "System Administrator",
            },
            {
                "username": "teacher",
                "email": "teacher@fluentian.com",
                "role": AppRole.teacher,
                "display_name": "Teacher",
            },
            {
                "username": "moderator",
                "email": "moderator@fluentian.com",
                "role": AppRole.moderator,
                "display_name": "Moderator",
            },
            {
                "username": "student",
                "email": "student@fluentian.com",
                "role": AppRole.student,
                "display_name": "Student User",
            },
        ]

        password = "Fluentian@12345"
        password_hash = hash_password(password)

        for user_data in users_to_create:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            if result.scalar_one_or_none():
                print(f"User {user_data['email']} already exists. Skipping...")
                continue

            # Create user
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=password_hash,
                role=user_data["role"],
                is_active=True,
                email_verified=True,
            )
            session.add(user)
            await session.flush()

            # Create profile and settings
            profile = UserProfile(
                user_id=user.id, display_name=user_data["display_name"]
            )
            settings = UserSettings(user_id=user.id)
            session.add(profile)
            session.add(settings)

            print(
                f"Created {user_data['role'].value} user: {user_data['email']} / {password}"
            )

        await session.commit()
        print("\nAll users seeded successfully!")


async def main():
    try:
        await create_database_if_not_exists()
        await seed_all_roles()
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
