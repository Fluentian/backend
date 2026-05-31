import asyncio

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import hash_password
from app.database import AsyncSessionLocal, engine
from app.models.user import AppRole, User, UserProfile, UserSettings


async def create_database_if_not_exists():
    # Connect to the default 'postgres' database to create the target database
    admin_url = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/postgres"
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


async def seed_admin():
    # Ensure tables are created
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if admin exists
        result = await session.execute(
            select(User).where(User.email == "admin@fluentian.com")
        )
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return

        # Create admin
        admin = User(
            username="admin",
            email="admin@fluentian.com",
            password_hash=hash_password("admin123"),
            role=AppRole.admin,
            is_active=True,
            email_verified=True,
        )
        session.add(admin)
        await session.flush()

        # Create profile and settings
        profile = UserProfile(user_id=admin.id, display_name="System Administrator")
        settings = UserSettings(user_id=admin.id)
        session.add(profile)
        session.add(settings)

        await session.commit()
        print("Admin user created: admin@fluentian.com / admin123")


async def main():
    try:
        await create_database_if_not_exists()
        await seed_admin()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
