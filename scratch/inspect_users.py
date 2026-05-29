import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:5432/fluentian")
    
    print("--- Users ---")
    users = await conn.fetch("SELECT id, username, email FROM users")
    for u in users:
        print(f"User: {u['username']} | Email: {u['email']} | ID: {u['id']}")
        
    print("\n--- Enrollments ---")
    enrollments = await conn.fetch("""
        SELECT e.user_id, u.username, e.course_id, c.code, e.is_active
        FROM course_enrollments e
        JOIN users u ON e.user_id = u.id
        JOIN courses c ON e.course_id = c.id
    """)
    for e in enrollments:
        print(f"User: {e['username']} | Course: {e['code']} | Active: {e['is_active']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
