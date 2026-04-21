"""
shared/utils.py — Utilidades comunes a todos los monitores.
"""
import functools
from datetime import datetime
from typing import Optional


@functools.lru_cache(maxsize=1)
def get_timezone():
    """Devuelve la zona horaria de Madrid. Resultado cacheado (singleton)."""
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
    """Devuelve el datetime actual en hora de Madrid."""
    return datetime.now(get_timezone())


def fmt_fecha_madrid(dt: Optional[datetime] = None) -> str:
    """Formatea fecha con hora y franja horaria de Madrid."""
    if dt is None:
        dt = now_madrid()
    return dt.strftime("%d/%m/%Y %H:%M %Z")
