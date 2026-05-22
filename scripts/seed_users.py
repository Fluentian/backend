import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User, AppRole
from app.core.security import hash_password

async def seed_users():
    async with AsyncSessionLocal() as db:
        roles_to_seed = [
            ("super_admin", "superadmin@fluentian.com", AppRole.super_admin),
            ("admin_test", "admin@fluentian.com", AppRole.admin),
            ("teacher_test", "teacher@fluentian.com", AppRole.teacher),
            ("moderator_test", "moderator@fluentian.com", AppRole.moderator),
            ("student_test", "student@fluentian.com", AppRole.student),
        ]

        for username, email, role in roles_to_seed:
            # Check if user already exists
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                print(f"Seeding user: {username} ({role.value})")
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=hash_password("password123"),
                    role=role,
                    is_active=True,
                    email_verified=True
                )
                db.add(new_user)
            else:
                print(f"User {email} already exists, updating role to {role.value}")
                existing_user.role = role
        
        await db.commit()
        print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_users())
