import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.content import Language, Course

async def check_and_seed():
    async with AsyncSessionLocal() as db:
        # Check languages
        result = await db.execute(select(Language))
        languages = result.scalars().all()
        print("Existing languages:")
        for lang in languages:
            print(f"- {lang.english_name} ({lang.iso_code}), ID: {lang.id}")

        if not languages:
            print("No languages found. Seeding French, English, and Amharic...")
            fr = Language(iso_code="fr", english_name="French", native_name="Français", is_active=True)
            en = Language(iso_code="en", english_name="English", native_name="English", is_active=True)
            am = Language(iso_code="am", english_name="Amharic", native_name="አማርኛ", is_active=True)
            db.add_all([fr, en, am])
            await db.commit()
            print("Languages seeded!")
            
            # Refresh languages
            result = await db.execute(select(Language))
            languages = result.scalars().all()
            for lang in languages:
                print(f"- {lang.english_name} ({lang.iso_code}), ID: {lang.id}")

        # Check courses
        result = await db.execute(select(Course))
        courses = result.scalars().all()
        print("\nExisting courses:")
        for course in courses:
            print(f"- {course.code} ({course.level_min} -> {course.level_max}), ID: {course.id}")

if __name__ == "__main__":
    asyncio.run(check_and_seed())
