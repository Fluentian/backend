from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text, case, and_, Float, cast
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, AppRole
from app.models.progress import UserLessonProgress, UserUnitProgress
from app.models.content import Lesson, PathUnit

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard", dependencies=[Depends(require_role(AppRole.admin))])
async def get_admin_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregated deep stats for the admin dashboard."""
    
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    
    # --- 1. Top Level Summary ---
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_completions = (await db.execute(select(func.count(UserLessonProgress.id)).where(UserLessonProgress.completed.is_(True)))).scalar() or 0
    avg_score = (await db.execute(select(func.avg(UserLessonProgress.mastery_score)).where(UserLessonProgress.completed.is_(True)))).scalar() or 0
    
    # Active users (last 7 days)
    active_users_7d = (await db.execute(select(func.count(User.id)).where(User.last_activity_date >= seven_days_ago))).scalar() or 0
    
    # --- 2. Growth & Activity Timeline ---
    reg_query = (
        select(func.date(User.created_at).label("date"), func.count(User.id).label("count"))
        .where(User.created_at >= thirty_days_ago)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    registrations = (await db.execute(reg_query)).all()
    
    activity_query = (
        select(
            func.date(UserLessonProgress.created_at).label("date"),
            func.count(UserLessonProgress.id).label("started"),
            func.count(case((UserLessonProgress.completed == True, 1))).label("completed")
        )
        .where(UserLessonProgress.created_at >= thirty_days_ago)
        .group_by(func.date(UserLessonProgress.created_at))
        .order_by(func.date(UserLessonProgress.created_at))
    )
    activity = (await db.execute(activity_query)).all()
    
    # --- 3. Conversion Funnel ---
    # Registered -> Completed 1 Lesson -> Completed 5 Lessons -> Completed 10+ Lessons
    has_1_lesson = (await db.execute(
        select(func.count(func.distinct(UserLessonProgress.user_id)))
        .where(UserLessonProgress.completed == True)
    )).scalar() or 0
    
    users_with_5 = (await db.execute(text("""
        SELECT count(*) FROM (
            SELECT user_id FROM user_lesson_progress 
            WHERE completed = true 
            GROUP BY user_id HAVING count(id) >= 5
        ) as sub
    """))).scalar() or 0

    users_with_10 = (await db.execute(text("""
        SELECT count(*) FROM (
            SELECT user_id FROM user_lesson_progress 
            WHERE completed = true 
            GROUP BY user_id HAVING count(id) >= 10
        ) as sub
    """))).scalar() or 0

    funnel = [
        {"stage": "Registered", "count": total_users},
        {"stage": "1+ Completed", "count": has_1_lesson},
        {"stage": "5+ Completed", "count": users_with_5},
        {"stage": "10+ Completed", "count": users_with_10},
    ]

    # --- 4. Retention (D1, D7) ---
    # D7 Retention: % of users who joined 7-14 days ago and were active in last 7 days
    joined_7_14_ago_query = select(func.count(User.id)).where(
        and_(User.created_at <= (now - timedelta(days=7)), User.created_at >= (now - timedelta(days=14)))
    )
    total_joined_7_14 = (await db.execute(joined_7_14_ago_query)).scalar() or 0
    
    retained_7_14_query = select(func.count(User.id)).where(
        and_(
            User.created_at <= (now - timedelta(days=7)), 
            User.created_at >= (now - timedelta(days=14)),
            User.last_activity_date >= seven_days_ago
        )
    )
    retained_7_14 = (await db.execute(retained_7_14_query)).scalar() or 0
    retention_7d = (retained_7_14 / total_joined_7_14 * 100) if total_joined_7_14 > 0 else 0

    # --- 5. Content Performance ---
    # Most dropped lessons (Started but low completion rate)
    dropoff_query = (
        select(
            Lesson.title,
            func.count(UserLessonProgress.id).label("started"),
            (cast(func.count(case((UserLessonProgress.completed == True, 1))), Float) / func.count(UserLessonProgress.id) * 100).label("rate")
        )
        .join(UserLessonProgress, UserLessonProgress.lesson_id == Lesson.id)
        .group_by(Lesson.title)
        .having(func.count(UserLessonProgress.id) > 5)
        .order_by(text("rate ASC"))
        .limit(5)
    )
    dropoffs = (await db.execute(dropoff_query)).all()

    # --- 6. XP Distribution ---
    xp_dist_query = text("""
        SELECT 
            CASE 
                WHEN xp_total = 0 THEN '0 XP'
                WHEN xp_total < 100 THEN '1-100 XP'
                WHEN xp_total < 500 THEN '100-500 XP'
                ELSE '500+ XP'
            END as range,
            count(*) as count
        FROM users
        GROUP BY 1
        ORDER BY 1
    """)
    xp_dist = (await db.execute(xp_dist_query)).all()

    return {
        "summary": {
            "total_users": total_users,
            "total_completions": total_completions,
            "average_score": round(float(avg_score), 1) if avg_score else 0,
            "active_users_7d": active_users_7d,
            "retention_7d_percent": round(retention_7d, 1)
        },
        "timeline": {
            "registrations": [{"date": str(r.date), "count": r.count} for r in registrations],
            "activity": [{"date": str(a.date), "started": a.started, "completed": a.completed} for a in activity],
        },
        "funnel": funnel,
        "content_performance": {
            "dropoffs": [{"title": d.title, "rate": round(d.rate, 1)} for d in dropoffs],
            "xp_distribution": [{"range": x.range, "count": x.count} for x in xp_dist]
        }
    }
