import os
import smtplib
from email.message import EmailMessage
from typing import Optional

from fb_core.creds_loader import logger


def _send_email_notification(to_email: Optional[str], subject: str, body: str) -> bool:
    """Send notification email using SMTP env configuration."""
    recipient = (to_email or "").strip()
    if not recipient:
        logger.warning("[EMAIL] skipped send due to missing recipient")
        return False

    admin_email = (os.getenv("ADMIN_EMAIL") or "").strip()
    admin_password = (os.getenv("ADMIN_PASSWORD") or "").strip()
    smtp_host = (os.getenv("SMTP_HOST") or "smtp.gmail.com").strip()
    smtp_port = int((os.getenv("SMTP_PORT") or "587").strip())
    smtp_use_tls = (os.getenv("SMTP_USE_TLS") or "true").strip().lower() == "true"

    if not admin_email or not admin_password:
        logger.warning("[EMAIL] skipped send because ADMIN_EMAIL/ADMIN_PASSWORD are not configured")
        return False

    try:
        msg = EmailMessage()
        msg["From"] = admin_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
            smtp.ehlo()
            if smtp_use_tls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(admin_email, admin_password)
            smtp.send_message(msg)

        logger.info("[EMAIL] sent to=%s subject=%s", recipient, subject)
        return True
    except Exception as error:
        logger.warning("[EMAIL] failed to send to=%s error=%s", recipient, error)
        return False