import asyncio
import asyncpg
import json
import uuid

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:5432/fluentian")
    
    lesson_id = "17a0b4bf-87e7-471c-8a2a-50f0c51c1228"
    
    print(f"Clearing old questions for lesson {lesson_id}...")
    await conn.execute("DELETE FROM questions WHERE lesson_id = $1", lesson_id)
    
    # We will seed 12 questions of different kinds
    questions = [
        # 1. mcq_single
        {
            "kind": "mcq_single",
            "prompt": {
                "question": "What is the French word for 'Apple'?",
                "options": ["Pomme", "Poire", "Orange", "Fraise"]
            },
            "grading": {
                "correct_answer": "Pomme"
            }
        },
        # 2. mcq_single with image
        {
            "kind": "mcq_single",
            "prompt": {
                "question": "What is shown in the image below?",
                "image_url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=600&q=80",
                "options": ["Un chien", "Un chat", "Un oiseau", "Un poisson"]
            },
            "grading": {
                "correct_answer": "Un chien"
            }
        },
        # 3. mcq_multi
        {
            "kind": "mcq_multi",
            "prompt": {
                "question": "Select all the French greetings (informal or formal):",
                "options": ["Bonjour", "Salut", "Fraise", "Bonsoir", "Chien"]
            },
            "grading": {
                "correct_answers": ["Bonjour", "Salut", "Bonsoir"]
            }
        },
        # 4. fill_blank (Choice chips)
        {
            "kind": "fill_blank",
            "prompt": {
                "question": "Comment ___ -tu ? (How are you?)",
                "options": ["vas", "est", "es", "as"]
            },
            "grading": {
                "correct_answer": "vas"
            }
        },
        # 5. fill_blank (Text Input)
        {
            "kind": "fill_blank",
            "prompt": {
                "question": "Je ___ un étudiant. (I am a student.)"
            },
            "grading": {
                "correct_answer": "suis"
            }
        },
        # 6. reorder
        {
            "kind": "reorder",
            "prompt": {
                "question": "Reorder the words to translate 'I would like a coffee':",
                "options": ["voudrais", "café", "Je", "un"]
            },
            "grading": {
                "correct_answer": "Je voudrais un café"
            }
        },
        # 7. match_pairs
        {
            "kind": "match_pairs",
            "prompt": {
                "question": "Match the pairs correctly:",
                "pairs": [
                    {"left": "Bonjour", "right": "Hello"},
                    {"left": "Au revoir", "right": "Goodbye"},
                    {"left": "Merci", "right": "Thank you"},
                    {"left": "Oui", "right": "Yes"}
                ]
            },
            "grading": {
                "pairs": [
                    {"left": "Bonjour", "right": "Hello"},
                    {"left": "Au revoir", "right": "Goodbye"},
                    {"left": "Merci", "right": "Thank you"},
                    {"left": "Oui", "right": "Yes"}
                ]
            }
        },
        # 8. short_text
        {
            "kind": "short_text",
            "prompt": {
                "question": "Translate 'Thank you very much' into French (with correct spacing):"
            },
            "grading": {
                "correct_answer": "Merci beaucoup"
            }
        },
        # 9. translation (Word Chips)
        {
            "kind": "translation",
            "prompt": {
                "question": "Translate: 'My name is Anwar'",
                "options": ["appelle", "pomme", "Je", "m'", "Anwar", "suis"]
            },
            "grading": {
                "correct_answer": "Je m'appelle Anwar"
            }
        },

        # 11. listening_comprehension
        {
            "kind": "listening_comprehension",
            "prompt": {
                "question": "Listen to the audio. What is the speaker's tone or topic?",
                "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
                "options": ["Greeting a friend", "Listening to music", "Ordering a meal"]
            },
            "grading": {
                "correct_answer": "Listening to music"
            }
        },
        # 12. dictation
        {
            "kind": "dictation",
            "prompt": {
                "question": "Listen and write down the sentence exactly:",
                "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
            },
            "grading": {
                "correct_answer": "Salut tout le monde"
            }
        }
    ]
    
    print("Seeding questions...")
    for i, q in enumerate(questions, 1):
        q_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO questions (id, lesson_id, question_kind, sequence_no, prompt_payload, grading_payload, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            """,
            q_id, lesson_id, q["kind"], i, json.dumps(q["prompt"]), json.dumps(q["grading"])
        )
        print(f"Added question {i} ({q['kind']})")
        
    print("Done seeding questions!")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
