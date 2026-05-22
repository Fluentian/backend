import csv
import io
import json
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.content import Course, PathUnit, Lesson, LessonBlock, Question, Language
from app.models.user import User

logger = logging.getLogger(__name__)

async def import_curriculum_csv(db: AsyncSession, csv_file: io.StringIO):
    reader = csv.DictReader(csv_file)
    
    # Store codes to map to IDs
    code_map = {} # code -> UUID
    
    # We need to find a default language for courses if not specified
    res = await db.execute(select(Language).limit(1))
    default_lang = res.scalar_one_or_none()
    if not default_lang:
        raise HTTPException(status_code=400, detail="No languages found in database. Seed languages first.")

    rows = list(reader)
    import_results = {"courses": 0, "units": 0, "lessons": 0, "blocks": 0, "questions": 0, "errors": []}

    # Pass 1: Courses
    for row in [r for r in rows if r['level'] == '0']:
        try:
            course = Course(
                code=row['code'],
                target_language_id=default_lang.id,
                level_min=row.get('level_min', 'A1'),
                level_max=row.get('level_max', 'A1'),
                is_published=True
            )
            db.add(course)
            await db.flush()
            code_map[row['code']] = course.id
            import_results["courses"] += 1
        except Exception as e:
            import_results["errors"].append(f"Error creating course {row.get('code')}: {str(e)}")

    # Pass 2: Units
    for row in [r for r in rows if r['level'] == '1']:
        parent_id = code_map.get(row['parent_code'])
        if not parent_id:
            import_results["errors"].append(f"Parent course {row['parent_code']} not found for unit {row['code']}")
            continue
        try:
            unit = PathUnit(
                course_id=parent_id,
                unit_kind=row.get('kind', 'core'),
                unit_no=int(row.get('sequence_no', 1)),
                title=row['title']
            )
            db.add(unit)
            await db.flush()
            code_map[row['code']] = unit.id
            import_results["units"] += 1
        except Exception as e:
            import_results["errors"].append(f"Error creating unit {row.get('code')}: {str(e)}")

    # Pass 3: Lessons
    for row in [r for r in rows if r['level'] == '2']:
        unit_id = code_map.get(row['parent_code'])
        if not unit_id:
            import_results["errors"].append(f"Parent unit {row['parent_code']} not found for lesson {row['code']}")
            continue
        
        # We also need the course_id for the lesson model
        res = await db.execute(select(PathUnit.course_id).where(PathUnit.id == unit_id))
        course_id = res.scalar()

        try:
            lesson = Lesson(
                course_id=course_id,
                unit_id=unit_id,
                lesson_kind=row.get('kind', 'grammar_explainer'),
                sequence_no=int(row.get('sequence_no', 1)),
                title=row['title'],
                estimated_minutes=int(row.get('estimated_minutes', 5)),
                xp_reward=int(row.get('xp', 10)),
                is_published=True
            )
            db.add(lesson)
            await db.flush()
            code_map[row['code']] = lesson.id
            import_results["lessons"] += 1
        except Exception as e:
            import_results["errors"].append(f"Error creating lesson {row.get('code')}: {str(e)}")

    # Pass 4: Blocks & Questions
    for row in [r for r in rows if r['level'] in ['3', '4']]:
        lesson_id = code_map.get(row['parent_code'])
        if not lesson_id:
            import_results["errors"].append(f"Parent lesson {row['parent_code']} not found for {row['type']} {row['code']}")
            continue

        try:
            payload = json.loads(row.get('payload', '{}'))
            if row['level'] == '3': # Block
                block = LessonBlock(
                    lesson_id=lesson_id,
                    block_kind=row.get('kind', 'text'),
                    sequence_no=int(row.get('sequence_no', 1)),
                    block_payload=payload
                )
                db.add(block)
                import_results["blocks"] += 1
            else: # Question
                grading = json.loads(row.get('grading_payload', '{}'))
                question = Question(
                    lesson_id=lesson_id,
                    question_kind=row.get('kind', 'mcq_single'),
                    sequence_no=int(row.get('sequence_no', 1)),
                    prompt_payload=payload,
                    grading_payload=grading
                )
                db.add(question)
                import_results["questions"] += 1
        except Exception as e:
            import_results["errors"].append(f"Error creating {row['type']} {row.get('code')}: {str(e)}")

    await db.commit()
    return import_results
