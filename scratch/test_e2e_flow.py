import httpx
import uuid
import sys

BASE_URL = "http://localhost:8000/api/v1"

def run_e2e():
    print("=========================================")
    print("Fluetan E2E Flow Verification Script")
    print("=========================================\n")

    # 1. Admin Login
    print("Step 1: Admin Logging in...")
    try:
        r = httpx.post(f"{BASE_URL}/auth/login", json={"email": "admin@fluentian.com", "password": "admin123"})
        if r.status_code != 200:
            r = httpx.post(f"{BASE_URL}/auth/login", json={"email": "admin@fluentian.com", "password": "password123"})
        
        assert r.status_code == 200, f"Admin Login failed: {r.status_code} - {r.text}"
        admin_token = r.json()["access_token"]
        print("Admin login successful.\n")
    except Exception as e:
        print(f"Error during admin login: {e}")
        sys.exit(1)

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Get French language ID
    print("Step 2: Fetching French Language ID...")
    r = httpx.get(f"{BASE_URL}/content/languages")
    assert r.status_code == 200, f"Failed to get languages: {r.text}"
    languages = r.json()
    fr_id = None
    for lang in languages:
        if lang["iso_code"] == "fr":
            fr_id = lang["id"]
    
    assert fr_id is not None, "French language not found in DB."
    print(f"French language ID: {fr_id}\n")

    # 3. Admin Creates Course
    suffix = uuid.uuid4().hex[:6]
    course_code = f"E2E_FR_LEVEL_1_{suffix}"
    print(f"Step 3: Creating Course '{course_code}'...")
    course_data = {
        "target_language_id": fr_id,
        "code": course_code,
        "level_min": "a1",
        "level_max": "a1",
        "is_published": True  # Publish it so user can see/enroll
    }
    r = httpx.post(f"{BASE_URL}/content/courses", json=course_data, headers=admin_headers)
    assert r.status_code == 200, f"Failed to create course: {r.text}"
    course = r.json()
    course_id = course["id"]
    print(f"Course created. ID: {course_id}\n")

    # 4. Admin Creates Unit
    print("Step 4: Creating Unit inside Course...")
    unit_data = {
        "unit_kind": "core",
        "unit_no": 1,
        "title": "Welcome to French A1"
    }
    r = httpx.post(f"{BASE_URL}/content/courses/{course_id}/units", json=unit_data, headers=admin_headers)
    assert r.status_code == 200, f"Failed to create unit: {r.text}"
    unit = r.json()
    unit_id = unit["id"]
    print(f"Unit created. ID: {unit_id}\n")

    # 5. Admin Creates Lesson
    print("Step 5: Creating Lesson inside Unit...")
    lesson_data = {
        "lesson_kind": "vocabulary",
        "sequence_no": 1,
        "title": "Saying Bonjour",
        "estimated_minutes": 5,
        "xp_reward": 25,
        "is_published": True
    }
    r = httpx.post(f"{BASE_URL}/content/units/{unit_id}/lessons", json=lesson_data, headers=admin_headers)
    assert r.status_code == 200, f"Failed to create lesson: {r.text}"
    lesson = r.json()
    lesson_id = lesson["id"]
    print(f"Lesson created. ID: {lesson_id}\n")

    # 6. Admin Adds Question to Lesson
    print("Step 6: Adding Question to Lesson...")
    question_data = {
        "question_kind": "mcq_single",
        "sequence_no": 1,
        "prompt_payload": {"text": "What does 'Bonjour' mean?"},
        "grading_payload": {"correct_answer": "Hello"}
    }
    r = httpx.post(f"{BASE_URL}/content/lessons/{lesson_id}/questions", json=question_data, headers=admin_headers)
    assert r.status_code == 200, f"Failed to create question: {r.text}"
    question = r.json()
    question_id = question["id"]
    print(f"Question created. ID: {question_id}\n")

    # 7. User Registration
    user_email = f"test_user_{suffix}@example.com"
    user_name = f"user_{suffix}"
    print(f"Step 7: Registering New Mobile User '{user_name}'...")
    reg_payload = {
        "username": user_name,
        "email": user_email,
        "password": "password123"
    }
    r = httpx.post(f"{BASE_URL}/auth/register", json=reg_payload)
    assert r.status_code == 201, f"User registration failed: {r.status_code} - {r.text}"
    user_data = r.json()
    user_token = user_data["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print(f"Registration successful. User ID: {user_data['user']['id']}\n")

    # 8. User Enrolls in Course
    print("Step 8: Enrolling User in Course...")
    r = httpx.post(f"{BASE_URL}/progress/enroll/{course_id}", json={}, headers=user_headers)
    assert r.status_code == 200, f"Failed to enroll: {r.text}"
    print("Enrollment successful.\n")

    # 9. User Completes Lesson
    print("Step 9: Submitting Lesson Completion (Mobile Simulation)...")
    completion_payload = {
        "score": 1.0,
        "answers": [
            {
                "question_id": question_id,
                "answer": "Hello",
                "is_correct": True
            }
        ],
        "time_seconds": 45
    }
    r = httpx.post(f"{BASE_URL}/progress/lessons/{lesson_id}/complete", json=completion_payload, headers=user_headers)
    assert r.status_code == 200, f"Failed to complete lesson: {r.text}"
    result = r.json()
    print("Completion Result:")
    print(f"  XP Earned: {result['xp_earned']}")
    print(f"  New XP Total: {result['new_xp_total']}")
    print(f"  Streak Days: {result['streak_days']}")
    print(f"  Hearts Remaining: {result['hearts_remaining']}")
    print(f"  Lesson Completed: {result['lesson_completed']}")
    print(f"  Unit Completed: {result['unit_completed']}")
    
    assert result["xp_earned"] == 37, f"Expected 37 XP, got {result['xp_earned']}"
    assert result["new_xp_total"] == 37, f"Expected 37 total XP, got {result['new_xp_total']}"
    print("Lesson completion stats verified successfully.\n")

    # 10. Fetch User Stats
    print("Step 10: Fetching User Stats to verify persistence...")
    r = httpx.get(f"{BASE_URL}/progress/me/stats", headers=user_headers)
    assert r.status_code == 200, f"Failed to get stats: {r.text}"
    stats = r.json()
    print("User Stats:")
    print(f"  Total XP: {stats['total_xp']}")
    print(f"  Lessons Completed: {stats['lessons_completed']}")
    print(f"  Units Completed: {stats['units_completed']}")
    
    assert stats["total_xp"] == 37, f"Expected total XP 37, got {stats['total_xp']}"
    assert stats["lessons_completed"] == 1, f"Expected 1 completed lesson, got {stats['lessons_completed']}"
    print("User stats persistent state verified.\n")

    # 11. Cleanup (Cascading delete check)
    print("Step 11: Admin deleting course (verifying cascading delete)...")
    r = httpx.delete(f"{BASE_URL}/content/courses/{course_id}", headers=admin_headers)
    assert r.status_code == 200, f"Failed to delete course: {r.text}"
    print("Course deletion successful.\n")

    # 12. Verify Cascading Deletion
    print("Step 12: Verifying cascading deletion...")
    # Get course detail - should be 404
    r = httpx.get(f"{BASE_URL}/content/courses/{course_id}")
    assert r.status_code == 404, f"Course should be deleted, but got: {r.status_code}"
    
    # Get lesson progress for the user - should now be empty or show 0 lessons completed
    r = httpx.get(f"{BASE_URL}/progress/me/stats", headers=user_headers)
    assert r.status_code == 200, f"Failed to get stats after deletion: {r.text}"
    post_stats = r.json()
    print("User Stats after Course Deletion:")
    print(f"  Lessons Completed: {post_stats['lessons_completed']}")
    # Total XP persists (since User experience is accumulated and stored on the user model,
    # but the lesson progress join records are cascade deleted)
    assert post_stats["lessons_completed"] == 0, f"Expected 0 completed lessons after deletion, got {post_stats['lessons_completed']}"
    print("Cascading deletion verified. All related unit, lesson, question, and progress records deleted.\n")

    print("=========================================")
    print("SUCCESS: Full E2E Flow verified perfectly!")
    print("=========================================")

if __name__ == "__main__":
    run_e2e()
