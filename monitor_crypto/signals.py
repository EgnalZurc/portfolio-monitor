"""
monitor_crypto/signals.py — Signal logic and staking date helpers.

Signals are evaluated in the context of staking decisions:
- Is it a good time to renew a fixed-term position?
- Should a flexible position be redeemed before a market correction?
- How close is the asset to its ATH (relevant for exit planning)?
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from shared.i18n import t

from .config import (
    ATH_DANGER_PCT, ATH_WARN_PCT,
    CHANGE_24H_DANGER, CHANGE_24H_PUMP, CHANGE_24H_WARN,
    CHANGE_30D_BEAR, CHANGE_30D_BULL,
    FG_EXTREME_FEAR, FG_EXTREME_GREED, FG_HIGH_GREED,
)


def days_until_available(pos: Dict[str, Any]) -> int:
    """Return days until the position can be redeemed or accessed."""
    today = datetime.now(timezone.utc).date()
    if pos["type"] == "fixed":
        maturity = datetime.fromisoformat(pos["maturity_date"]).date()
        return max(0, (maturity - today).days)
    return pos["rescue_days"]


def next_distribution_in(pos: Dict[str, Any]) -> Optional[int]:
    """Return days until the next staking reward distribution."""
    if "next_distribution" not in pos:
        return None
    today = datetime.now(timezone.utc).date()
    nd    = datetime.fromisoformat(pos["next_distribution"]).date()
    freq  = pos.get("distribution_freq_days", 1)
    while nd < today:
        nd += timedelta(days=freq)
    return (nd - today).days


def compute_signals(
    pos: Dict[str, Any],
    price_data: Dict[str, Any],
    market_data: Dict[str, Any],
    fear_greed_val: Optional[int],
) -> List[Tuple[str, str]]:
    """Compute signals for a position. Returns list of (type, message)."""
    signals    = []
    cg_id      = pos["coingecko_id"]
    price_info = price_data.get(cg_id, {})
    change_24h = price_info.get("eur_24h_change", 0)
    ath_pct    = market_data.get("ath_change_pct")
    change_30d = market_data.get("price_change_30d")

    # Fear & Greed signals
    if fear_greed_val is not None:
        if fear_greed_val >= FG_EXTREME_GREED:
            signals.append(("danger",  t("crypto.fg_extreme_greed", val=fear_greed_val)))
        elif fear_greed_val >= FG_HIGH_GREED:
            signals.append(("warning", t("crypto.fg_high_greed",    val=fear_greed_val)))
        elif fear_greed_val <= FG_EXTREME_FEAR:
            signals.append(("success", t("crypto.fg_extreme_fear",  val=fear_greed_val)))

    # 24h price change signals
    if change_24h is not None:
        if change_24h <= CHANGE_24H_DANGER:
            signals.append(("danger",  t("crypto.drop_danger", pct=change_24h)))
        elif change_24h <= CHANGE_24H_WARN:
            signals.append(("warning", t("crypto.drop_warn",   pct=change_24h)))
        elif change_24h >= CHANGE_24H_PUMP:
            signals.append(("warning", t("crypto.pump_warn",   pct=change_24h)))

    # ATH proximity signals
    if ath_pct is not None:
        if ath_pct >= ATH_DANGER_PCT:
            signals.append(("danger",  t("crypto.ath_danger", pct=abs(ath_pct))))
        elif ath_pct >= ATH_WARN_PCT:
            signals.append(("warning", t("crypto.ath_warn",   pct=abs(ath_pct))))

    # 30-day momentum signals
    if change_30d is not None:
        if change_30d <= CHANGE_30D_BEAR:
            signals.append(("warning", t("crypto.bear_30d", pct=change_30d)))
        elif change_30d >= CHANGE_30D_BULL:
            signals.append(("success", t("crypto.bull_30d", pct=change_30d)))

    return signals
