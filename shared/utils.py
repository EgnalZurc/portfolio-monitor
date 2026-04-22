"""
shared/utils.py — Shared timezone and date formatting utilities.
"""
import functools
from datetime import datetime
from typing import Optional


@functools.lru_cache(maxsize=1)
def get_timezone():
    """Return the Madrid timezone object. Result is cached (singleton)."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Madrid")
    except ImportError:
        try:
            import pytz
            return pytz.timezone("Europe/Madrid")
        except ImportError:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytz", "-q"])
            import pytz
            return pytz.timezone("Europe/Madrid")


def now_madrid() -> datetime:
    """Return the current datetime in Madrid timezone."""
    return datetime.now(get_timezone())


def fmt_fecha_madrid(dt: Optional[datetime] = None) -> str:
    """Format a datetime as a human-readable string in Madrid timezone."""
    if dt is None:
        dt = now_madrid()
    return dt.strftime("%d/%m/%Y %H:%M %Z")
