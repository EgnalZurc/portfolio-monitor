"""
monitor_etf/analysis.py — Market data download and technical analysis.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import html as _html
import numpy as np
import pandas as pd
import yfinance as yf

from shared.i18n import t

from .config import (
    ALERTA_CAIDA_DESDE_MAX, ALERTA_PERDIDA_REAL, ALERTA_VENTA_CRITICA,
    CARTERA, MM_CORTA, MM_LARGA, PLAN,
)
from .models import AlertLevel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plan helpers
# ---------------------------------------------------------------------------

def current_phase() -> str:
    """Return the current investment phase label (translated)."""
    today = datetime.today()
    if today >= PLAN["fecha_cambio_fase"]:
        return t("etf.phase2")
    months = int((PLAN["fecha_cambio_fase"] - today).days / 30.44)
    return t("etf.phase1", months=months)


def current_contribution(fund_id: str) -> float:
    """Return the active monthly contribution for a fund."""
    cfg = CARTERA.get(fund_id, {})
    if datetime.today() >= PLAN["fecha_cambio_fase"]:
        return cfg.get("aportacion_fase2", 0.0)
    return cfg.get("aportacion_mes", 0.0)


def years_since_start() -> int:
    """Return years elapsed since the first ETF purchase."""
    try:
        start = datetime.fromisoformat(list(CARTERA.values())[0]["inicio"])
        return max(1, round((datetime.today() - start).days / 365))
    except (ValueError, KeyError, IndexError) as e:
        logger.warning(t("etf.error_years", exc=e))
        return 1


def projected_milestone(fund_id: str) -> Optional[float]:
    """Return the projected EUR milestone for the current year."""
    try:
        from shared.settings import _FUND_IDS
        milestones  = PLAN["hitos"]
        year        = min(years_since_start(), max(milestones.keys()))
        milestone   = milestones.get(year)
        if milestone is None:
            return None
        idx = _FUND_IDS.index(fund_id) if fund_id in _FUND_IDS else 0
        return milestone[idx] if idx < len(milestone) else None
    except (KeyError, IndexError, TypeError, ValueError) as e:
        logger.warning(t("etf.error_hito", etf_id=fund_id, exc=e))
        return None


def compare_vs_projection(
    fund_id: str,
    current_price: float,
    units: float,
    avg_cost: Optional[float],
) -> Optional[Dict[str, Any]]:
    """Compare current portfolio value against the projected milestone."""
    milestone = projected_milestone(fund_id)
    if not milestone or not avg_cost or units <= 0:
        return None
    portfolio_value = current_price * units
    return {
        "expected":  milestone,
        "actual":    portfolio_value,
        "deviation": (portfolio_value / milestone - 1) if milestone > 0 else 0,
        "year":      years_since_start(),
    }


# ---------------------------------------------------------------------------
# Data download
# ---------------------------------------------------------------------------

def fetch_etf_data(ticker_sym: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Download one year of historical data and fast_info for an ETF."""
    try:
        ticker = yf.Ticker(ticker_sym)
        hist   = ticker.history(period="1y")
        if hist.empty:
            logger.warning(t("etf.hist_empty", ticker=ticker_sym))
            return pd.DataFrame(), {}
        info = {}
        try:
            info = ticker.fast_info
        except (AttributeError, KeyError, ValueError):
            logger.debug(f"Fast info not available for {ticker_sym}")
        return hist, info
    except Exception as e:
        logger.error(t("etf.error_download", ticker=ticker_sym, exc=f"{type(e).__name__}: {e}"))
        raise


# ---------------------------------------------------------------------------
# Signal analysis helpers
# ---------------------------------------------------------------------------

def _analyse_moving_averages(
    hist: pd.DataFrame,
    price: float,
    ma50: Optional[float],
    ma200: Optional[float],
    signals: List,
    level: AlertLevel,
) -> Tuple[List, AlertLevel]:
    """Analyse moving average positions and recent crossovers."""
    if not (ma50 and ma200):
        return signals, level
    if price < ma200:
        signals.append((t("signal.mm200.title"), t("signal.mm200.body", price=price, mm=ma200), "WARN"))
        level = level.escalate(AlertLevel.WARN)
    elif price < ma50:
        signals.append((t("signal.mm50.title"), t("signal.mm50.body", price=price, mm=ma50), "INFO"))
        level = level.escalate(AlertLevel.INFO)
    else:
        signals.append((t("signal.mm_ok.title"), t("signal.mm_ok.body", price=price, mm50=ma50, mm200=ma200), "OK"))
    try:
        prev_ma50  = float(hist["Close"].rolling(MM_CORTA).mean().iloc[-2]) if len(hist) > MM_CORTA else None
        prev_ma200 = float(hist["Close"].rolling(MM_LARGA).mean().iloc[-2]) if len(hist) > MM_LARGA else None
        if prev_ma50 and prev_ma200:
            if prev_ma50 <= prev_ma200 and ma50 > ma200:
                signals.append((t("signal.golden.title"), t("signal.golden.body"), "INFO"))
                level = level.escalate(AlertLevel.INFO)
            elif prev_ma50 >= prev_ma200 and ma50 < ma200:
                signals.append((t("signal.death.title"), t("signal.death.body"), "DANGER"))
                level = AlertLevel.DANGER
    except (IndexError, ValueError, TypeError):
        logger.debug("Error calculating MA crossovers")
    return signals, level


def _analyse_drawdown_and_cost(
    price: float,
    high_52w: float,
    drawdown: float,
    avg_cost: Optional[float],
    signals: List,
    level: AlertLevel,
) -> Tuple[List, AlertLevel]:
    """Analyse drawdown from 52-week high and position vs average cost."""
    if drawdown < ALERTA_VENTA_CRITICA:
        signals.append((t("signal.drop_severe.title"), t("signal.drop_severe.body", pct=drawdown, high=high_52w), "DANGER"))
        level = AlertLevel.DANGER
    elif drawdown < ALERTA_CAIDA_DESDE_MAX:
        signals.append((t("signal.drop_warn.title"), t("signal.drop_warn.body", pct=drawdown, high=high_52w), "WARN"))
        level = level.escalate(AlertLevel.WARN)
    if avg_cost and avg_cost > 0:
        pct = (price / avg_cost) - 1
        if pct < ALERTA_VENTA_CRITICA:
            signals.append((t("signal.loss_crit.title"), t("signal.loss_crit.body", pct=pct, avg=avg_cost), "DANGER"))
            level = AlertLevel.DANGER
        elif pct < ALERTA_PERDIDA_REAL:
            signals.append((t("signal.loss_warn.title"), t("signal.loss_warn.body", pct=pct, avg=avg_cost), "WARN"))
            level = level.escalate(AlertLevel.WARN)
        elif pct >= 0:
            signals.append((t("signal.profit.title"), t("signal.profit.body", pct=pct, avg=avg_cost), "OK"))
    return signals, level


def calculate_signals(
    hist: pd.DataFrame,
    avg_cost: Optional[float],
) -> Dict[str, Any]:
    """Calculate all technical signals for an ETF. Returns a result dict."""
    empty: Dict[str, Any] = {
        "price": 0, "high_52w": 0, "low_52w": 0,
        "chg_1d": 0, "chg_1m": 0, "chg_3m": 0, "chg_ytd": 0,
        "ma50": None, "ma200": None, "drawdown": 0,
        "pct_vs_cost": None, "annual_vol": 0,
        "signals": [], "level": AlertLevel.OK, "hist": hist,
    }
    if hist.empty or len(hist) < 2:
        logger.warning(t("etf.hist_insufficient"))
        return empty

    # Extend history if needed to compute long-term MA
    if len(hist) < MM_LARGA:
        try:
            ext = yf.Ticker(hist.index.name or "").history(period="2y")
            if not ext.empty and len(ext) > len(hist):
                hist = ext
        except Exception as e:
            logger.debug(f"Could not extend history: {e}")

    price   = float(hist["Close"].iloc[-1])
    high_52w = float(hist["High"].max())
    low_52w  = float(hist["Low"].min())

    chg_1d  = (hist["Close"].iloc[-1] / hist["Close"].iloc[-2]  - 1) if len(hist) > 1  else 0
    chg_1m  = (hist["Close"].iloc[-1] / hist["Close"].iloc[-22] - 1) if len(hist) > 22 else 0
    chg_3m  = (hist["Close"].iloc[-1] / hist["Close"].iloc[-66] - 1) if len(hist) > 66 else 0

    # Year-to-date return
    try:
        ytd_mask  = hist.index.year == datetime.now(timezone.utc).year
        ytd_idx   = hist[ytd_mask].index[0] if any(ytd_mask) else hist.index[0]
        ytd_price = float(hist["Close"].loc[ytd_idx] if ytd_idx in hist.index else hist["Close"].iloc[0])
        chg_ytd   = (hist["Close"].iloc[-1] / ytd_price - 1) if ytd_price else 0
    except (IndexError, KeyError, TypeError):
        chg_ytd = 0

    # Moving averages
    _v50  = hist["Close"].rolling(MM_CORTA).mean().iloc[-1] if len(hist) >= MM_CORTA else None
    _v200 = hist["Close"].rolling(MM_LARGA).mean().iloc[-1] if len(hist) >= MM_LARGA else None
    ma50  = float(_v50)  if _v50  is not None and not pd.isna(_v50)  else None
    ma200 = float(_v200) if _v200 is not None and not pd.isna(_v200) else None
    drawdown = (price / high_52w) - 1 if high_52w > 0 else 0

    signals: List[Tuple[str, str, str]] = []
    level = AlertLevel.OK
    signals, level = _analyse_moving_averages(hist, price, ma50, ma200, signals, level)
    signals, level = _analyse_drawdown_and_cost(price, high_52w, drawdown, avg_cost, signals, level)
    pct_vs_cost = (price / avg_cost - 1) if avg_cost and avg_cost > 0 else None

    annual_vol = 0.0
    try:
        returns    = hist["Close"].pct_change().dropna()
        annual_vol = float(returns.std() * np.sqrt(252))
        if annual_vol > 0.30:
            signals.append((t("signal.volatility.title"), t("signal.volatility.body", vol=annual_vol), "INFO"))
    except (ValueError, TypeError) as e:
        logger.debug(t("etf.error_volatility", exc=e))

    return {
        "price": price, "high_52w": high_52w, "low_52w": low_52w,
        "chg_1d": chg_1d, "chg_1m": chg_1m, "chg_3m": chg_3m, "chg_ytd": chg_ytd,
        "ma50": ma50, "ma200": ma200, "drawdown": drawdown,
        "pct_vs_cost": pct_vs_cost, "annual_vol": annual_vol,
        "signals": signals, "level": level, "hist": hist,
    }


def recommendation(level: AlertLevel, name: str) -> Tuple[str, str, str]:
    """Return (title, body, colour) recommendation based on alert level."""
    if not name or not isinstance(name, str):
        name = "ETF"
    safe_name = _html.escape(name)
    if level == AlertLevel.DANGER:
        return (t("rec.danger.title"), t("rec.danger.body", name=safe_name), "#C0392B")
    if level == AlertLevel.WARN:
        return (t("rec.warn.title"),   t("rec.warn.body",   name=safe_name), "#F0A500")
    return     (t("rec.ok.title"),     t("rec.ok.body",     name=safe_name), "#1A7A4A")
