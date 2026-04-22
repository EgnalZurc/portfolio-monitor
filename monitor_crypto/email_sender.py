"""
monitor_crypto/email_sender.py — SMTP delivery for the crypto report.
Delivery logic (when to send vs save) lives in shared/delivery.py.
"""
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from shared.i18n import t
from shared.config_loader import EMAIL_CONFIG

logger = logging.getLogger(__name__)


def send_email(html_content: str) -> None:
    """Send the crypto HTML report by email."""
    try:
        date = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        msg  = MIMEMultipart("alternative")
        msg["Subject"] = t("email.subject_crypto", date=date)
        msg["From"]    = EMAIL_CONFIG["user"]
        msg["To"]      = EMAIL_CONFIG["recipient"]
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(EMAIL_CONFIG["user"], EMAIL_CONFIG["password"])
            server.sendmail(EMAIL_CONFIG["user"], EMAIL_CONFIG["recipient"], msg.as_string())
        logger.info(t("email.sent"))
    except smtplib.SMTPAuthenticationError as e:
        logger.error(t("email.error_auth", exc=e))
    except smtplib.SMTPException as e:
        logger.error(t("email.error_smtp", exc=e))
    except (ConnectionError, TimeoutError) as e:
        logger.error(t("email.error_conn", exc=e))
    except Exception as e:
        logger.error(t("email.error_unexpected", exc=f"{type(e).__name__}: {e}"))
