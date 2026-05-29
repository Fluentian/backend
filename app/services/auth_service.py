"""Authentication service — registration, login, token management."""

import logging
import secrets
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import PWD_RESET_TTL_SECONDS, REDIS_PWD_RESET_PREFIX, REDIS_REFRESH_PREFIX
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)

# from app.models.subscription import Subscription, SubscriptionTier
from app.models.user import User, UserProfile, UserSettings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


async def _get_redis() -> redis.Redis:
    """Lazy-initialise the Redis client."""
    global _redis_client  # noqa: PLW0603
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def register_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    ui_language_id: UUID | None = None,
) -> tuple[User, str, str]:
    """Register a new user, returning (user, access_token, refresh_token)."""
    # Check uniqueness
    existing = await db.execute(
        select(User).where((User.email == email) | (User.username == username))
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("A user with this email or username already exists")

    # Create user + profile + settings + subscription in one transaction
    async with db.begin_nested():
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            ui_language_id=ui_language_id,
        )
        db.add(user)
        await db.flush()

        profile = UserProfile(user_id=user.id, display_name=username)
        settings_obj = UserSettings(user_id=user.id)
        # subscription = Subscription(user_id=user.id, tier=SubscriptionTier.free)

        db.add_all([profile, settings_obj])

    await db.commit()
    await db.refresh(user)

    # Generate tokens
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store refresh token hash in Redis
    await _store_refresh_token(user.id, refresh_token)

    return user, access_token, refresh_token


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str, str]:
    """Authenticate user, returning (user, access_token, refresh_token)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")

    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    await _store_refresh_token(user.id, refresh_token)

    return user, access_token, refresh_token


async def refresh_tokens(
    db: AsyncSession,
    raw_refresh_token: str,
) -> tuple[User, str, str]:
    """Validate a refresh token and issue a new token pair."""
    payload = decode_token(raw_refresh_token)
    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    user_id = UUID(payload["sub"])

    # Verify token exists in Redis
    try:
        r = await _get_redis()
        token_hash = hash_token(raw_refresh_token)
        key = f"{REDIS_REFRESH_PREFIX}:{user_id}:{token_hash}"
        if not await r.exists(key):
            raise UnauthorizedError("Refresh token has been revoked")

        # Delete old token
        await r.delete(key)
    except Exception as e:
        if settings.DEBUG:
            logger.warning(f"Redis unavailable, skipping revocation check: {e}")
        else:
            raise

    # Load user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or deactivated")

    # Issue new pair
    token_data = {"sub": str(user.id)}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    await _store_refresh_token(user.id, new_refresh)

    return user, new_access, new_refresh


async def logout_user(user_id: UUID, raw_refresh_token: str | None = None) -> None:
    """Revoke a refresh token in Redis. Skips if Redis is unavailable in dev."""
    if raw_refresh_token:
        try:
            r = await _get_redis()
            token_hash = hash_token(raw_refresh_token)
            key = f"{REDIS_REFRESH_PREFIX}:{user_id}:{token_hash}"
            await r.delete(key)
        except Exception as e:
            if settings.DEBUG:
                logger.warning(f"Redis unavailable, skipping token revocation: {e}")
            else:
                raise
    else:
        # Delete all refresh tokens for user
        try:
            r = await _get_redis()
            pattern = f"{REDIS_REFRESH_PREFIX}:{user_id}:*"
            async for key in r.scan_iter(match=pattern):
                await r.delete(key)
        except Exception as e:
            if settings.DEBUG:
                logger.warning(f"Redis unavailable, skipping bulk token revocation: {e}")
            else:
                raise


async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """Generate a password reset code. Returns code only in debug mode."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # Don't reveal whether email exists
        return None

    code = secrets.token_urlsafe(32)
    r = await _get_redis()
    key = f"{REDIS_PWD_RESET_PREFIX}:{user.id}"
    await r.set(key, code, ex=PWD_RESET_TTL_SECONDS)

    if settings.DEBUG:
        return code
    return None


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    """Validate reset token and update the password."""
    r = await _get_redis()

    # Search for the token across all users
    found_user_id: UUID | None = None
    async for key in r.scan_iter(match=f"{REDIS_PWD_RESET_PREFIX}:*"):
        stored_code = await r.get(key)
        if stored_code == token:
            user_id_str = key.split(":")[-1]
            found_user_id = UUID(user_id_str)
            await r.delete(key)
            break

    if found_user_id is None:
        raise NotFoundError("Invalid or expired reset token")

    result = await db.execute(select(User).where(User.id == found_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    user.password_hash = hash_password(new_password)
    await db.commit()


# ── Internal helpers ────────────────────────────────────


async def _store_refresh_token(user_id: UUID, raw_token: str) -> None:
    """Store refresh token hash in Redis with TTL. Skips if Redis is unavailable in dev."""
    try:
        r = await _get_redis()
        token_hash = hash_token(raw_token)
        key = f"{REDIS_REFRESH_PREFIX}:{user_id}:{token_hash}"
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await r.set(key, "1", ex=ttl)
    except Exception as e:
        if settings.DEBUG:
            logger.warning(f"Redis unavailable, skipping token storage: {e}")
        else:
            raise
