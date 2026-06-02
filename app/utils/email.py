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
    """Send OTP email for signup or password reset via Brevo with premium HTML design."""
    if purpose == "signup":
        subject = "✨ Verify your Fluentian Account"
        title = "Verify Your Email"
        subtitle = "Welcome to Fluentian! Confirm your email address to get started."
        icon = "✉️"
        color_accent = "#6366f1"
        color_light = "#f0f4ff"
    else:
        subject = "🔐 Reset Your Fluentian Password"
        title = "Reset Your Password"
        subtitle = "We received a password reset request. Use the code below to secure your account."
        icon = "🔑"
        color_accent = "#f59e0b"
        color_light = "#fffbeb"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                color: #1a202c;
                line-height: 1.6;
                min-height: 100vh;
                padding: 20px 0;
            }}
            .wrapper {{
                max-width: 600px;
                margin: 0 auto;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            }}
            .header {{
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                padding: 60px 40px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200px;
                height: 200px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
            }}
            .header::after {{
                content: '';
                position: absolute;
                bottom: -40%;
                left: -40%;
                width: 150px;
                height: 150px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
            }}
            .logo {{
                position: relative;
                z-index: 1;
                color: #ffffff;
                font-size: 32px;
                font-weight: 800;
                letter-spacing: 2px;
                margin-bottom: 8px;
                text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .tagline {{
                color: rgba(255, 255, 255, 0.85);
                font-size: 13px;
                letter-spacing: 1px;
                text-transform: uppercase;
                font-weight: 600;
            }}
            .content {{
                padding: 50px 40px;
                text-align: center;
            }}
            .icon {{
                font-size: 48px;
                margin-bottom: 20px;
            }}
            .title {{
                font-size: 28px;
                font-weight: 700;
                color: #1a202c;
                margin-bottom: 12px;
                letter-spacing: -0.5px;
            }}
            .subtitle {{
                font-size: 16px;
                color: #64748b;
                margin-bottom: 40px;
                line-height: 1.5;
            }}
            .otp-wrapper {{
                margin: 40px 0;
            }}
            .otp-label {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #94a3b8;
                font-weight: 700;
                margin-bottom: 16px;
            }}
            .otp-container {{
                background: linear-gradient(135deg, {color_light} 0%, #ffffff 100%);
                border: 2px solid {color_accent};
                border-radius: 16px;
                padding: 32px;
                margin-bottom: 0;
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.1);
            }}
            .otp-code {{
                font-size: 48px;
                font-weight: 900;
                color: {color_accent};
                letter-spacing: 12px;
                font-family: 'Monaco', 'Courier New', monospace;
                margin: 0;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }}
            .otp-timer {{
                font-size: 13px;
                color: #e11d48;
                margin-top: 16px;
                font-weight: 600;
            }}
            .security-note {{
                background-color: #f0fdf4;
                border: 1px solid #dcfce7;
                border-left: 4px solid #22c55e;
                border-radius: 10px;
                padding: 16px;
                margin: 32px 0;
            }}
            .security-note-title {{
                color: #15803d;
                font-weight: 700;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            .security-note-text {{
                color: #166534;
                font-size: 13px;
                line-height: 1.5;
            }}
            .divider {{
                height: 1px;
                background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
                margin: 32px 0;
            }}
            .support-text {{
                font-size: 13px;
                color: #94a3b8;
                margin: 24px 0 0 0;
            }}
            .support-link {{
                color: {color_accent};
                text-decoration: none;
                font-weight: 600;
            }}
            .footer {{
                background-color: #f8fafc;
                border-top: 1px solid #e2e8f0;
                padding: 40px;
                text-align: center;
            }}
            .footer-text {{
                font-size: 12px;
                color: #94a3b8;
                margin-bottom: 8px;
            }}
            .footer-links {{
                font-size: 12px;
            }}
            .footer-link {{
                color: #64748b;
                text-decoration: none;
                margin: 0 12px;
            }}
            .footer-link:hover {{
                color: {color_accent};
                text-decoration: underline;
            }}
            @media (max-width: 600px) {{
                .content {{
                    padding: 32px 24px;
                }}
                .header {{
                    padding: 40px 24px;
                }}
                .title {{
                    font-size: 24px;
                }}
                .otp-code {{
                    font-size: 36px;
                    letter-spacing: 8px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="container">
                <!-- Header -->
                <div class="header">
                    <div class="logo">FLUENTIAN</div>
                    <div class="tagline">Learn French. Gain Confidence.</div>
                </div>

                <!-- Content -->
                <div class="content">
                    <div class="icon">{icon}</div>
                    <h1 class="title">{title}</h1>
                    <p class="subtitle">{subtitle}</p>

                    <!-- OTP Code -->
                    <div class="otp-wrapper">
                        <div class="otp-label">Your Verification Code</div>
                        <div class="otp-container">
                            <div class="otp-code">{otp}</div>
                            <div class="otp-timer">⏱️ Expires in 10 minutes</div>
                        </div>
                    </div>

                    <!-- Security Note -->
                    <div class="security-note">
                        <div class="security-note-title">🛡️ Security Tip</div>
                        <div class="security-note-text">Never share this code with anyone. Fluentian support will never ask for your verification code.</div>
                    </div>

                    <div class="divider"></div>

                    <p class="support-text">
                        Didn't request this? <a href="mailto:support@fluentian.binovatechnologies.com" class="support-link">Contact support</a>
                    </p>
                </div>

                <!-- Footer -->
                <div class="footer">
                    <div class="footer-text">© {datetime.now().year} Fluentian. All rights reserved.</div>
                    <div class="footer-links">
                        <a href="https://fluentianapp.binovatechnologies.com" class="footer-link">Login</a>
                        <a href="https://fluentianapp.binovatechnologies.com/help" class="footer-link">Help Center</a>
                        <a href="mailto:support@fluentian.binovatechnologies.com" class="footer-link">Support</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(subject, to_email, html_content)


async def send_admin_credentials_email(
    email: str,
    username: str,
    password: str,
    role: str,
    recipient_name: str | None = None,
) -> bool:
    """Send account credentials email to newly created admin/staff user with premium design."""
    display_name = recipient_name or username
    role_display = role.replace("_", " ").title()

    # Role-specific styling
    role_colors = {
        "super_admin": ("#dc2626", "#fee2e2"),
        "admin": ("#ea580c", "#ffedd5"),
        "teacher": ("#2563eb", "#dbeafe"),
        "moderator": "#10b981",
        "student": "#6b7280",
    }

    primary_color, bg_light = role_colors.get(role, ("#6366f1", "#f0f4ff"))

    subject = f"🎉 Welcome {display_name}! Your Fluentian Account is Ready"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                color: #1a202c;
                line-height: 1.6;
                min-height: 100vh;
                padding: 20px 0;
            }}
            .wrapper {{
                max-width: 650px;
                margin: 0 auto;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            }}
            .header {{
                background: linear-gradient(135deg, {primary_color} 0%, {primary_color}cc 100%);
                padding: 60px 40px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200px;
                height: 200px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
            }}
            .header::after {{
                content: '';
                position: absolute;
                bottom: -40%;
                left: -40%;
                width: 150px;
                height: 150px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
            }}
            .logo {{
                position: relative;
                z-index: 1;
                color: #ffffff;
                font-size: 32px;
                font-weight: 800;
                letter-spacing: 2px;
                margin-bottom: 8px;
                text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .tagline {{
                color: rgba(255, 255, 255, 0.85);
                font-size: 13px;
                letter-spacing: 1px;
                text-transform: uppercase;
                font-weight: 600;
            }}
            .content {{
                padding: 50px 40px;
            }}
            .welcome-icon {{
                font-size: 48px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .title {{
                font-size: 28px;
                font-weight: 700;
                color: #1a202c;
                margin-bottom: 8px;
                text-align: center;
                letter-spacing: -0.5px;
            }}
            .greeting {{
                font-size: 16px;
                color: #64748b;
                margin-bottom: 8px;
                text-align: center;
            }}
            .greeting-name {{
                color: {primary_color};
                font-weight: 700;
            }}
            .role-info {{
                background: linear-gradient(135deg, {bg_light} 0%, #ffffff 100%);
                border: 2px solid {primary_color};
                border-radius: 12px;
                padding: 20px;
                margin: 32px 0;
                text-align: center;
            }}
            .role-label {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                color: #64748b;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .role-badge {{
                display: inline-block;
                background: linear-gradient(135deg, {primary_color} 0%, {primary_color}dd 100%);
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
            }}
            .credentials-title {{
                font-size: 16px;
                font-weight: 700;
                color: #1a202c;
                margin-top: 32px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .credentials-box {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 0;
                overflow: hidden;
            }}
            .credential-item {{
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
            }}
            .credential-item:last-child {{
                border-bottom: none;
            }}
            .credential-label {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                color: #64748b;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .credential-value {{
                font-size: 18px;
                font-weight: 700;
                color: {primary_color};
                font-family: 'Monaco', 'Courier New', monospace;
                word-break: break-all;
                background: #ffffff;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            }}
            .cta-section {{
                margin-top: 40px;
                text-align: center;
                padding-top: 32px;
                border-top: 2px solid #e2e8f0;
            }}
            .cta-text {{
                font-size: 15px;
                color: #64748b;
                margin-bottom: 16px;
            }}
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, {primary_color} 0%, {primary_color}dd 100%);
                color: #ffffff;
                padding: 14px 40px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: 700;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
                transition: all 0.3s ease;
            }}
            .cta-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
            }}
            .next-steps {{
                background: #fff7ed;
                border: 1px solid #fed7aa;
                border-left: 4px solid #f59e0b;
                border-radius: 10px;
                padding: 20px;
                margin: 32px 0;
            }}
            .next-steps-title {{
                font-weight: 700;
                color: #92400e;
                margin-bottom: 12px;
                font-size: 15px;
            }}
            .next-steps-list {{
                list-style: none;
                margin: 0;
            }}
            .next-steps-list li {{
                color: #b45309;
                font-size: 14px;
                margin-bottom: 8px;
                padding-left: 24px;
                position: relative;
            }}
            .next-steps-list li:last-child {{
                margin-bottom: 0;
            }}
            .next-steps-list li::before {{
                content: '✓';
                position: absolute;
                left: 0;
                color: #f59e0b;
                font-weight: 700;
            }}
            .security-warning {{
                background: #fee2e2;
                border: 1px solid #fecaca;
                border-left: 4px solid #dc2626;
                border-radius: 10px;
                padding: 16px;
                margin: 24px 0;
            }}
            .security-warning-title {{
                color: #991b1b;
                font-weight: 700;
                margin-bottom: 6px;
                font-size: 13px;
            }}
            .security-warning-text {{
                color: #b91c1c;
                font-size: 13px;
                line-height: 1.5;
            }}
            .divider {{
                height: 2px;
                background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
                margin: 32px 0;
            }}
            .footer {{
                background-color: #f8fafc;
                border-top: 1px solid #e2e8f0;
                padding: 40px;
                text-align: center;
            }}
            .footer-text {{
                font-size: 12px;
                color: #94a3b8;
                margin-bottom: 12px;
            }}
            .footer-links {{
                font-size: 12px;
            }}
            .footer-link {{
                color: #64748b;
                text-decoration: none;
                margin: 0 12px;
            }}
            .footer-link:hover {{
                color: {primary_color};
                text-decoration: underline;
            }}
            @media (max-width: 600px) {{
                .content {{
                    padding: 32px 24px;
                }}
                .header {{
                    padding: 40px 24px;
                }}
                .title {{
                    font-size: 24px;
                }}
                .credential-value {{
                    font-size: 16px;
                }}
                .cta-button {{
                    padding: 12px 32px;
                    font-size: 14px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="container">
                <!-- Header -->
                <div class="header">
                    <div class="logo">FLUENTIAN</div>
                    <div class="tagline">Learn French. Gain Confidence.</div>
                </div>

                <!-- Content -->
                <div class="content">
                    <div class="welcome-icon">🎓</div>
                    <h1 class="title">Your Account is Ready!</h1>
                    <div class="greeting">
                        Welcome, <span class="greeting-name">{display_name}</span> 👋
                    </div>

                    <!-- Role Information -->
                    <div class="role-info">
                        <div class="role-label">Your Account Role</div>
                        <span class="role-badge">{role_display}</span>
                    </div>

                    <!-- Credentials Section -->
                    <div class="credentials-title">Login Credentials</div>
                    <div class="credentials-box">
                        <div class="credential-item">
                            <div class="credential-label">📧 Email Address</div>
                            <div class="credential-value">{email}</div>
                        </div>
                        <div class="credential-item">
                            <div class="credential-label">🔐 Temporary Password</div>
                            <div class="credential-value">{password}</div>
                        </div>
                    </div>

                    <!-- Next Steps -->
                    <div class="next-steps">
                        <div class="next-steps-title">📌 Getting Started</div>
                        <ul class="next-steps-list">
                            <li>Visit <strong>fluentianapp.binovatechnologies.com</strong> to log in</li>
                            <li>Use the credentials above to access your account</li>
                            <li>Change your password on first login for security</li>
                            <li>Complete your profile and start learning!</li>
                        </ul>
                    </div>

                    <!-- Call to Action -->
                    <div class="cta-section">
                        <div class="cta-text">Ready to get started?</div>
                        <a href="https://fluentianapp.binovatechnologies.com" class="cta-button">Login Now</a>
                    </div>

                    <!-- Security Warning -->
                    <div class="security-warning">
                        <div class="security-warning-title">🛡️ Important Security Notice</div>
                        <div class="security-warning-text">
                            This is a temporary password. <strong>Change it immediately</strong> after your first login. Keep your credentials confidential and never share them with anyone.
                        </div>
                    </div>

                    <div class="divider"></div>

                    <p style="font-size: 13px; color: #64748b; text-align: center; margin: 0;">
                        Questions? <a href="mailto:support@fluentian.binovatechnologies.com" style="color: {primary_color}; text-decoration: none; font-weight: 600;">Contact our support team</a>
                    </p>
                </div>

                <!-- Footer -->
                <div class="footer">
                    <div class="footer-text">© {datetime.now().year} Fluentian. All rights reserved.</div>
                    <div class="footer-text" style="font-size: 11px; color: #cbd5e1;">noreply@fluentian.binovatechnologies.com</div>
                    <div class="footer-links" style="margin-top: 12px;">
                        <a href="https://fluentianapp.binovatechnologies.com" class="footer-link">Platform</a>
                        <a href="https://fluentianapp.binovatechnologies.com/help" class="footer-link">Help Center</a>
                        <a href="mailto:support@fluentian.binovatechnologies.com" class="footer-link">Support</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(subject, email, html_content)
