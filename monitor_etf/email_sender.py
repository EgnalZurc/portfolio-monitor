"""
monitor_etf/email_sender.py — SMTP delivery for the ETF report.
Delivery logic (when to send vs save) lives in shared/report_delivery.py.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from shared.i18n import t
from shared.settings import EMAIL_CONFIG

logger = logging.getLogger(__name__)


def send_email(html_content: str) -> None:
    """Send the ETF HTML report by email."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = t("email.subject_etf")
        msg["From"]    = EMAIL_CONFIG["usuario"]
        msg["To"]      = EMAIL_CONFIG["destinatario"]
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=10) as server:
            server.login(EMAIL_CONFIG["usuario"], EMAIL_CONFIG["password"])
            server.sendmail(EMAIL_CONFIG["usuario"], EMAIL_CONFIG["destinatario"], msg.as_string())
        logger.info(t("email.sent"))
    except smtplib.SMTPAuthenticationError as e:
        logger.error(t("email.error_auth", exc=e))
    except smtplib.SMTPException as e:
        logger.error(t("email.error_smtp", exc=e))
    except (ConnectionError, TimeoutError) as e:
        logger.error(t("email.error_conn", exc=e))
    except Exception as e:
        logger.error(t("email.error_unexpected", exc=f"{type(e).__name__}: {e}"))
