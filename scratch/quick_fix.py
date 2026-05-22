import asyncio
import asyncpg

async def run():
    conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:5432/fluentian")
    try:
        print("Altering table lessons...")
        await conn.execute("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()")
        await conn.execute("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()")
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
