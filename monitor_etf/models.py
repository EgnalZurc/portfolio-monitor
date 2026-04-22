"""
monitor_etf/models.py — Enumerations and types for the ETF monitor.
"""
from enum import Enum

from shared.i18n import t


class AlertLevel(Enum):
    """Alert levels with associated display properties."""
    OK     = ("OK",     "#1A7A4A", "#E8F5E9", "alert.ok",     "✅")
    INFO   = ("INFO",   "#3A7BD5", "#E8F0FB", "alert.info",   "ℹ️")
    WARN   = ("WARN",   "#F0A500", "#FFF3CD", "alert.warn",   "⚠️")
    DANGER = ("DANGER", "#C0392B", "#FDECEA", "alert.danger", "🚨")

    @property
    def color(self) -> str:
        return self.value[1]

    @property
    def background(self) -> str:
        return self.value[2]

    @property
    def label(self) -> str:
        """Return the translated label for the current language."""
        return t(self.value[3])

    @property
    def emoji(self) -> str:
        return self.value[4]

    def escalate(self, other: "AlertLevel") -> "AlertLevel":
        """Return the more severe of two alert levels."""
        rank = {AlertLevel.OK: 0, AlertLevel.INFO: 1,
                AlertLevel.WARN: 2, AlertLevel.DANGER: 3}
        return self if rank[self] >= rank[other] else other
