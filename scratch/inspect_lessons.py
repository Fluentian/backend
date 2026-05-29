import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:5432/fluentian")
    
    print("--- Courses ---")
    courses = await conn.fetch("SELECT id, code, target_language_id, is_published FROM courses")
    for c in courses:
        print(f"Course: {c['code']} | ID: {c['id']} | LangID: {c['target_language_id']}")
        
    print("\n--- Units ---")
    units = await conn.fetch("SELECT id, course_id, title, unit_no, unit_kind FROM path_units ORDER BY unit_no")
    for u in units:
        print(f"Unit {u['unit_no']} ({u['title']}) | ID: {u['id']} | CourseID: {u['course_id']} | Kind: {u['unit_kind']}")
        
    print("\n--- Lessons ---")
    lessons = await conn.fetch("SELECT id, unit_id, title, sequence_no, lesson_kind FROM lessons ORDER BY unit_id, sequence_no")
    for l in lessons:
        print(f"Lesson {l['sequence_no']}: {l['title']} ({l['lesson_kind']}) | ID: {l['id']} | UnitID: {l['unit_id']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
