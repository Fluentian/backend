import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:5432/fluentian")
    
    print("--- Questions ---")
    questions = await conn.fetch("SELECT id, lesson_id, question_kind, sequence_no, prompt_payload, grading_payload FROM questions ORDER BY lesson_id, sequence_no")
    for q in questions:
        print(f"ID: {q['id']}")
        print(f"Lesson ID: {q['lesson_id']}")
        print(f"Kind: {q['question_kind']}")
        print(f"Sequence: {q['sequence_no']}")
        print(f"Prompt Payload: {json.dumps(json.loads(q['prompt_payload']), indent=2)}")
        print(f"Grading Payload: {json.dumps(json.loads(q['grading_payload']), indent=2)}")
        print("-" * 40)
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
