import httpx
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def test_flow():
    # 1. Login
    print("Testing login...")
    try:
        r = httpx.post(f"{BASE_URL}/auth/login", json={"email": "admin@fluentian.com", "password": "admin123"})
        if r.status_code != 200:
            # Try other password from seed_users
            r = httpx.post(f"{BASE_URL}/auth/login", json={"email": "admin@fluentian.com", "password": "password123"})
        
        assert r.status_code == 200, f"Login failed: {r.status_code} - {r.text}"
        data = r.json()
        token = data["access_token"]
        print("Logged in successfully. Token acquired.")
    except Exception as e:
        print(f"Error during login: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get languages to get FR language ID
    print("\nFetching languages...")
    r = httpx.get(f"{BASE_URL}/content/languages")
    assert r.status_code == 200, f"Failed to get languages: {r.text}"
    languages = r.json()
    fr_id = None
    for lang in languages:
        if lang["iso_code"] == "fr":
            fr_id = lang["id"]
    
    assert fr_id is not None, "French language not found in DB."
    print(f"French language ID: {fr_id}")

    # 3. Create course
    print("\nCreating new course...")
    course_data = {
        "target_language_id": fr_id,
        "code": f"TEST_FR_COURSE_{uuid.uuid4().hex[:8]}",
        "level_min": "a1",
        "level_max": "a2",
        "is_published": False
    }
    r = httpx.post(f"{BASE_URL}/content/courses", json=course_data, headers=headers)
    assert r.status_code == 200, f"Failed to create course: {r.text}"
    course = r.json()
    course_id = course["id"]
    print(f"Course created with ID: {course_id}, Code: {course['code']}")

    # 4. Patch course
    print("\nUpdating course details...")
    update_data = {
        "level_max": "b1",
        "is_published": True
    }
    r = httpx.patch(f"{BASE_URL}/content/courses/{course_id}", json=update_data, headers=headers)
    assert r.status_code == 200, f"Failed to update course: {r.text}"
    updated_course = r.json()
    assert updated_course["level_max"] == "b1"
    assert updated_course["is_published"] is True
    print(f"Course updated successfully! level_max: {updated_course['level_max']}, is_published: {updated_course['is_published']}")

    # 5. Create unit
    print("\nCreating unit...")
    unit_data = {
        "unit_kind": "core",
        "unit_no": 1,
        "title": "Introduction to Test Course"
    }
    r = httpx.post(f"{BASE_URL}/content/courses/{course_id}/units", json=unit_data, headers=headers)
    assert r.status_code == 200, f"Failed to create unit: {r.text}"
    unit = r.json()
    unit_id = unit["id"]
    print(f"Unit created with ID: {unit_id}, Title: {unit['title']}")

    # 6. Create lesson
    print("\nCreating lesson...")
    lesson_data = {
        "lesson_kind": "vocabulary",
        "sequence_no": 1,
        "title": "Greeting in French",
        "estimated_minutes": 5,
        "xp_reward": 10,
        "is_published": True
    }
    r = httpx.post(f"{BASE_URL}/content/units/{unit_id}/lessons", json=lesson_data, headers=headers)
    assert r.status_code == 200, f"Failed to create lesson: {r.text}"
    lesson = r.json()
    lesson_id = lesson["id"]
    print(f"Lesson created with ID: {lesson_id}, Title: {lesson['title']}")

    # 7. Delete lesson
    print("\nDeleting lesson...")
    r = httpx.delete(f"{BASE_URL}/content/lessons/{lesson_id}", headers=headers)
    assert r.status_code == 200, f"Failed to delete lesson: {r.text}"
    print("Lesson deleted successfully.")

    # 8. Delete course
    print("\nDeleting course...")
    r = httpx.delete(f"{BASE_URL}/content/courses/{course_id}", headers=headers)
    assert r.status_code == 200, f"Failed to delete course: {r.text}"
    print("Course deleted successfully.")

    print("\nAll endpoints verified successfully!")

if __name__ == "__main__":
    test_flow()
