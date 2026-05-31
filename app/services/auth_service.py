"""Authentication service — registration, login, token management."""

import logging
import random
import secrets
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import (
    OTP_TTL_SECONDS,
    PWD_RESET_TTL_SECONDS,
    REDIS_OTP_RESET_PREFIX,
    REDIS_OTP_SIGNUP_PREFIX,
    REDIS_PWD_RESET_PREFIX,
    REDIS_REFRESH_PREFIX,
)
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationError
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
from app.utils.email import send_otp_email

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


async def _get_redis() -> redis.Redis:
    """Lazy-initialise the Redis client."""
    global _redis_client  # noqa: PLW0603
    if _redis_client is None or settings.APP_ENV == "testing":
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def register_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    ui_language_id: UUID | None = None,
) -> tuple[User, str | None]:
    """Register a new user, generating an OTP and sending verification email."""
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
            email_verified=False,
        )
        db.add(user)
        await db.flush()

        profile = UserProfile(user_id=user.id, display_name=username)
        settings_obj = UserSettings(user_id=user.id)
        # subscription = Subscription(user_id=user.id, tier=SubscriptionTier.free)

        db.add_all([profile, settings_obj])

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    
    # Store OTP in Redis
    r = await _get_redis()
    key = f"{REDIS_OTP_SIGNUP_PREFIX}:{email}"
    await r.set(key, otp, ex=OTP_TTL_SECONDS)

    # Send verification email
    email_sent = await send_otp_email(email, otp, "signup")
    if not email_sent:
        raise ValidationError("Failed to send verification email. Please check the email server configuration.")

    await db.commit()
    await db.refresh(user)

    if settings.DEBUG or settings.APP_ENV == "testing":
        return user, otp
    return user, None


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

    if not user.email_verified:
        # Generate 6-digit OTP
        otp = f"{random.randint(100000, 999999)}"
        r = await _get_redis()
        key = f"{REDIS_OTP_SIGNUP_PREFIX}:{email}"
        await r.set(key, otp, ex=OTP_TTL_SECONDS)
        
        # Send verification email
        email_sent = await send_otp_email(email, otp, "signup")
        if not email_sent:
            raise ValidationError("Failed to send verification email. Please check the email server configuration.")
        raise UnauthorizedError("Email not verified", detail=email)

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


async def verify_signup_otp(
    db: AsyncSession,
    email: str,
    otp: str,
) -> tuple[User, str, str]:
    """Verify signup OTP, set email_verified to True, and generate JWT tokens."""
    r = await _get_redis()
    key = f"{REDIS_OTP_SIGNUP_PREFIX}:{email}"
    stored_otp = await r.get(key)

    if not stored_otp or stored_otp != otp:
        raise ValidationError("Invalid or expired verification code")

    await r.delete(key)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    user.email_verified = True
    await db.commit()
    await db.refresh(user)

    # Generate tokens since verification succeeded
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store refresh token hash in Redis
    await _store_refresh_token(user.id, refresh_token)

    return user, access_token, refresh_token


async def resend_signup_otp(
    db: AsyncSession,
    email: str,
) -> None:
    """Resend a new signup OTP to the user's email."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    if user.email_verified:
        raise ConflictError("Email is already verified")

    # Generate a new 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    
    # Store OTP in Redis
    r = await _get_redis()
    key = f"{REDIS_OTP_SIGNUP_PREFIX}:{email}"
    await r.set(key, otp, ex=OTP_TTL_SECONDS)

    # Send verification email
    email_sent = await send_otp_email(email, otp, "signup")
    if not email_sent:
        raise ValidationError("Failed to send verification email. Please check the email server configuration.")


async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """Generate a password reset 6-digit OTP. Returns OTP only in debug mode."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # Don't reveal whether email exists
        return None

    otp = f"{random.randint(100000, 999999)}"
    r = await _get_redis()
    key = f"{REDIS_OTP_RESET_PREFIX}:{email}"
    await r.set(key, otp, ex=OTP_TTL_SECONDS)

    # Send reset email
    email_sent = await send_otp_email(email, otp, "reset_password")
    if not email_sent:
        raise ValidationError("Failed to send password reset email. Please check the email server configuration.")

    if settings.DEBUG:
        return otp
    return None


async def reset_password(db: AsyncSession, email: str, token: str, new_password: str) -> None:
    """Validate reset OTP and update the password."""
    r = await _get_redis()
    key = f"{REDIS_OTP_RESET_PREFIX}:{email}"
    stored_otp = await r.get(key)

    if not stored_otp or stored_otp != token:
        raise ValidationError("Invalid or expired reset code")

    await r.delete(key)

    result = await db.execute(select(User).where(User.email == email))
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
