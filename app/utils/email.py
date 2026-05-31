"""Email utility for sending emails via Brevo Transactional Email API."""

import logging
from datetime import datetime

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Brevo API endpoint
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_email(subject: str, recipient: str, html_content: str) -> bool:
    """Send an email using Brevo Transactional Email API asynchronously."""
    if settings.APP_ENV == "testing":
        logger.info(f"Skipping actual email send to {recipient} in testing environment")
        return True

    if not settings.BREVO_API_KEY:
        logger.error("BREVO_API_KEY is not configured")
        return False

    payload = {
        "sender": {
            "name": settings.MAIL_FROM_NAME,
            "email": settings.MAIL_FROM_EMAIL,
        },
        "to": [
            {
                "email": recipient,
                "name": recipient,
            }
        ],
        "subject": subject,
        "htmlContent": html_content,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                BREVO_API_URL,
                json=payload,
                headers={
                    "api-key": settings.BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
            )

            if response.status_code in (200, 201):
                logger.info(f"Email sent successfully to {recipient}")
                return True
            else:
                logger.error(
                    f"Failed to send email to {recipient}: "
                    f"status={response.status_code}, response={response.text}"
                )
                return False

    except httpx.RequestError as e:
        logger.error(f"Request error while sending email to {recipient}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while sending email to {recipient}: {e}")
        return False


async def send_otp_email(to_email: str, otp: str, purpose: str) -> bool:
    """Send OTP email for signup or password reset via Brevo."""
    if purpose == "signup":
        subject = "Verify your Fluentian Account"
        title = "Verify your email address"
        subtitle = "Thank you for signing up for Fluentian! Please use the verification code below to complete your registration."
        btn_text = "Verification Code"
    else:
        subject = "Reset your Fluentian Password"
        title = "Reset your password"
        subtitle = "We received a request to reset your password. Use the code below to set a new password."
        btn_text = "Reset Code"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f9fafb;
                margin: 0;
                padding: 0;
                color: #1f2937;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                border: 1px solid #e5e7eb;
            }}
            .header {{
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                padding: 32px;
                text-align: center;
            }}
            .logo {{
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            .content {{
                padding: 40px 32px;
                text-align: center;
            }}
            h1 {{
                font-size: 24px;
                font-weight: 700;
                color: #111827;
                margin-top: 0;
                margin-bottom: 16px;
            }}
            p {{
                font-size: 16px;
                line-height: 24px;
                color: #4b5563;
                margin-bottom: 32px;
            }}
            .otp-container {{
                background-color: #f3f4f6;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 32px;
                border: 1px dashed #c7d2fe;
                display: inline-block;
            }}
            .otp-label {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                color: #6b7280;
                margin-bottom: 8px;
                font-weight: 600;
            }}
            .otp-code {{
                font-size: 36px;
                font-weight: 800;
                color: #4f46e5;
                letter-spacing: 8px;
                margin: 0;
            }}
            .footer {{
                background-color: #f9fafb;
                padding: 24px;
                text-align: center;
                border-top: 1px solid #e5e7eb;
                font-size: 12px;
                color: #9ca3af;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">Fluentian</div>
            </div>
            <div class="content">
                <h1>{title}</h1>
                <p>{subtitle}</p>
                <div class="otp-container">
                    <div class="otp-label">{btn_text}</div>
                    <div class="otp-code">{otp}</div>
                </div>
                <p style="font-size: 14px; margin-bottom: 0;">This code will expire in 10 minutes. If you did not request this email, please ignore it.</p>
            </div>
            <div class="footer">
                &copy; {datetime.now().year} Fluentian. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(subject, to_email, html_content)
