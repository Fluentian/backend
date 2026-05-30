"""App-wide constants for the Fluentian backend."""

# ── API Versioning ──────────────────────────────────────
API_V1_PREFIX = "/api/v1"

# ── Pagination ──────────────────────────────────────────
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ── Hearts ──────────────────────────────────────────────
FREE_TIER_MAX_HEARTS = 5
PLUS_TIER_MAX_HEARTS = 10
PRO_TIER_UNLIMITED_HEARTS = -1  # sentinel for unlimited

HEART_REFILL_INTERVAL_HOURS = 4

# ── XP ──────────────────────────────────────────────────
XP_MULTIPLIER_PERFECT = 1.5
XP_MULTIPLIER_GOOD = 1.0
XP_MULTIPLIER_PASS = 0.5
XP_MULTIPLIER_FAIL = 0.0
PASS_THRESHOLD = 0.6

# ── Password ────────────────────────────────────────────
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# ── Gemini AI ───────────────────────────────────────────
MAX_CONVERSATION_HISTORY = 50
MAX_EXPLANATION_WORDS = 150

# ── Redis key prefixes ─────────────────────────────────
REDIS_REFRESH_PREFIX = "refresh"
REDIS_PWD_RESET_PREFIX = "pwd_reset"
REDIS_OTP_SIGNUP_PREFIX = "otp_signup"
REDIS_OTP_RESET_PREFIX = "otp_reset"
PWD_RESET_TTL_SECONDS = 900  # 15 minutes
OTP_TTL_SECONDS = 600  # 10 minutes
