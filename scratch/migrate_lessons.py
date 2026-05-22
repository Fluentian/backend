import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Altering lessons table to add created_at and updated_at...")
        try:
            await conn.execute(text("ALTER TABLE lessons ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL"))
            await conn.execute(text("ALTER TABLE lessons ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW()"))
            print("Successfully altered lessons table.")
        except Exception as e:
            print(f"Error altering table: {e}")
            print("Trying to check if columns already exist...")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
