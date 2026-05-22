import asyncio
from sqlalchemy import select
from app.database import engine
from app.models.content import Language

async def list_langs():
    async with engine.connect() as conn:
        result = await conn.execute(select(Language))
        langs = result.all()
        for l in langs:
            print(f"ID: {l.id} | Code: {l.iso_code} | Name: {l.english_name}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(list_langs())
