#!/usr/bin/env python3
"""
Test script for Brevo email sending.

This script tests the email sending functionality via Brevo Transactional Email API.
Run from the backend directory with: python scripts/test_email.py

Example:
    python scripts/test_email.py test@example.com
    python scripts/test_email.py test@example.com "Test Subject" "Test HTML content"
"""

import asyncio
import logging
import sys

# Add backend to path
sys.path.insert(0, "/home/beki/Desktop/Fluentian-contributors/backend")

from app.config import settings
from app.utils.email import send_email, send_otp_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_send_email(
    recipient: str, subject: str = None, html_content: str = None
) -> None:
    """Test sending a regular email."""
    if subject is None:
        subject = "Test Email from Fluentian"
    if html_content is None:
        html_content = """
        <html>
            <body>
                <h2>Test Email</h2>
                <p>This is a test email sent via Brevo API.</p>
                <p><strong>Timestamp:</strong> Test email sent from backend test script.</p>
            </body>
        </html>
        """

    logger.info(f"Sending test email to {recipient}...")
    result = await send_email(subject, recipient, html_content)
    if result:
        logger.info(f"✓ Email sent successfully to {recipient}")
    else:
        logger.error(f"✗ Failed to send email to {recipient}")
    return result


async def test_send_otp_email(recipient: str, purpose: str = "signup") -> None:
    """Test sending an OTP email."""
    test_otp = "123456"
    logger.info(f"Sending OTP email to {recipient} for purpose: {purpose}...")
    result = await send_otp_email(recipient, test_otp, purpose)
    if result:
        logger.info(f"✓ OTP email sent successfully to {recipient} (OTP: {test_otp})")
    else:
        logger.error(f"✗ Failed to send OTP email to {recipient}")
    return result


async def main() -> None:
    """Main test runner."""
    logger.info("=" * 60)
    logger.info("Fluentian Email Service Test")
    logger.info("=" * 60)

    # Validate configuration
    logger.info("\n--- Configuration Check ---")
    if not settings.BREVO_API_KEY:
        logger.error("✗ BREVO_API_KEY is not configured in .env")
        sys.exit(1)
    logger.info(f"✓ BREVO_API_KEY configured: {settings.BREVO_API_KEY[:20]}...")
    logger.info(f"✓ MAIL_FROM_EMAIL: {settings.MAIL_FROM_EMAIL}")
    logger.info(f"✓ MAIL_FROM_NAME: {settings.MAIL_FROM_NAME}")

    # Get recipient from command line or use default
    if len(sys.argv) > 1:
        recipient = sys.argv[1]
    else:
        logger.warning("No recipient provided. Using default test recipient.")
        recipient = "test@binova.tech"

    logger.info(f"\nRecipient: {recipient}")
    logger.info(f"Environment: {settings.APP_ENV}")

    # Test 1: Send regular email
    logger.info("\n--- Test 1: Send Regular Email ---")
    await test_send_email(recipient)

    # Test 2: Send signup OTP email
    logger.info("\n--- Test 2: Send Signup OTP Email ---")
    await test_send_otp_email(recipient, "signup")

    # Test 3: Send password reset OTP email
    logger.info("\n--- Test 3: Send Password Reset OTP Email ---")
    await test_send_otp_email(recipient, "reset_password")

    logger.info("\n" + "=" * 60)
    logger.info("Test completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
