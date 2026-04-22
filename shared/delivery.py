"""
shared/delivery.py — HTML report delivery logic.

Behaviour:
  - No email credentials → save HTML to disk (fallback for local debugging)
  - Email credentials present + --generate-html flag → save to disk AND send email
  - Email credentials present, no flag → send email only (default CI behaviour)
"""
import logging
import sys
import webbrowser
from pathlib import Path
from typing import Callable

from shared.i18n import t
from shared.config_loader import EMAIL_CONFIG

logger = logging.getLogger(__name__)

_GENERATE_HTML_FLAG = "--generate-html"


def _email_configured() -> bool:
    """Return True if Gmail credentials are available."""
    return bool(EMAIL_CONFIG["user"] and EMAIL_CONFIG["password"])


def _save_to_disk(html: str, path: Path) -> bool:
    """Write HTML to disk. Returns True on success."""
    try:
        path.write_text(html, encoding="utf-8")
        logger.info(t("delivery.saved", path=path.resolve()))
        return True
    except IOError as e:
        logger.error(t("delivery.save_error", exc=e))
        return False


def _open_browser(path: Path) -> None:
    """Open a local HTML file in the default browser."""
    try:
        webbrowser.open(path.resolve().as_uri())
        logger.info(t("etf.opening_browser"))
    except Exception as e:
        logger.warning(f"Could not open browser: {e}")


def deliver_report(
    html: str,
    output_path: Path,
    send_fn: Callable[[str], None],
) -> None:
    """
    Deliver an HTML report according to the configured behaviour.

    Args:
        html:        The rendered HTML string.
        output_path: Destination path when saving to disk.
        send_fn:     Callable that sends the HTML string by email.
    """
    generate_html = _GENERATE_HTML_FLAG in sys.argv
    email_ready   = _email_configured()

    if not email_ready:
        logger.info(t("delivery.no_creds_fallback"))
        if _save_to_disk(html, output_path):
            _open_browser(output_path)
        return

    if generate_html:
        _save_to_disk(html, output_path)

    send_fn(html)
