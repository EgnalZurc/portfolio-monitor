"""
shared/settings.py — Loads settings.toml and exposes typed configuration.

All monitors import from here. To change any value, edit settings.toml.
Credentials are read exclusively from environment variables.
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# TOML loading — tomllib (Python 3.11+) or tomli fallback
# ---------------------------------------------------------------------------
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        print("ERROR: Install 'tomli' for Python < 3.11:  pip install tomli")
        sys.exit(1)

_ROOT      = Path(__file__).parent.parent
_TOML_PATH = _ROOT / "settings.toml"

if not _TOML_PATH.exists():
    print(
        f"ERROR: settings.toml not found at {_TOML_PATH}\n"
        "Copy settings.example.toml to settings.toml and fill in your values."
    )
    sys.exit(1)

with open(_TOML_PATH, "rb") as _f:
    _S = tomllib.load(_f)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(path: str, default: Any = None) -> Any:
    """Dot-separated key access into the loaded TOML dict."""
    node = _S
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

LANG: str = os.environ.get("MONITOR_LANG", _get("general.lang", "es")).lower()


# ---------------------------------------------------------------------------
# Email — credentials come exclusively from environment variables / secrets
# ---------------------------------------------------------------------------

_gmail_user = os.environ.get("GMAIL_USER", "").strip()
_gmail_pass = os.environ.get("GMAIL_PASS", "").strip()
_to_email   = os.environ.get("TO_EMAIL",   _gmail_user).strip()

EMAIL_CONFIG: Dict[str, Any] = {
    "smtp_server":  "smtp.gmail.com",
    "smtp_port":    465,
    # ETF monitor keys
    "usuario":      _gmail_user,
    "password":     _gmail_pass,
    "destinatario": _to_email,
    # Crypto monitor keys
    "gmail_user":   _gmail_user,
    "gmail_pass":   _gmail_pass,
    "to_email":     _to_email,
}


# ---------------------------------------------------------------------------
# ETF — Portfolio  (built dynamically from [[etf.funds]] array)
# ---------------------------------------------------------------------------

def _build_etf_entry(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert one [[etf.funds]] TOML entry into the runtime dict."""
    inicio       = raw.get("inicio", "").strip()
    precio_medio = raw.get("precio_medio", 0.0)
    return {
        "ticker":           raw.get("ticker",           ""),
        "nombre":           raw.get("name",             raw.get("id", "")),
        "isin":             raw.get("isin",             ""),
        "precio_medio":     precio_medio if precio_medio > 0 else None,
        "participaciones":  raw.get("participaciones",  0.0),
        "aportacion_mes":   raw.get("aportacion_mes",   0.0),
        "aportacion_fase2": raw.get("aportacion_fase2", 0.0),
        "inicio":           inicio or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "color":            raw.get("color",            "#3A7BD5"),
    }


# CARTERA is an ordered dict keyed by the fund's id field.
# Adding a new [[etf.funds]] block in settings.toml is all that is needed.
CARTERA: Dict[str, Dict[str, Any]] = {
    fund["id"]: _build_etf_entry(fund)
    for fund in _get("etf.funds", [])
    if "id" in fund
}

# Ordered list of fund IDs — used to map milestone tuples by position
_FUND_IDS: List[str] = list(CARTERA.keys())


# ---------------------------------------------------------------------------
# ETF — Investment plan
# ---------------------------------------------------------------------------

_plan_raw   = _get("etf.plan", {})
_milestones = _get("etf.plan.milestones", {})

PLAN: Dict[str, Any] = {
    "fecha_cambio_fase": datetime.fromisoformat(
        _plan_raw.get("phase_change_date", "2027-03-01")
    ),
    # Milestones keyed by int year; values are tuples matching _FUND_IDS order
    "hitos": {int(k): tuple(v) for k, v in _milestones.items()},
    # IRPF tax brackets — sentinel 999_999_999 becomes float("inf")
    "irpf_tramos": [
        (float("inf") if limit >= 999_999_999 else float(limit), rate)
        for limit, rate in _get("etf.tax.brackets", [])
    ],
}


# ---------------------------------------------------------------------------
# ETF — Technical thresholds
# ---------------------------------------------------------------------------

_thr = _get("etf.thresholds", {})

MM_CORTA:               int   = _thr.get("ma_short",            50)
MM_LARGA:               int   = _thr.get("ma_long",             200)
ALERTA_CAIDA_DESDE_MAX: float = _thr.get("drop_from_high_warn", -0.15)
ALERTA_PERDIDA_REAL:    float = _thr.get("loss_vs_cost_warn",   -0.10)
ALERTA_VENTA_CRITICA:   float = _thr.get("critical_threshold",  -0.20)


# ---------------------------------------------------------------------------
# Crypto — Positions  (built dynamically from [[crypto.positions]] array)
# ---------------------------------------------------------------------------

POSITIONS: List[Dict[str, Any]] = _get("crypto.positions", [])


# ---------------------------------------------------------------------------
# Crypto — Signal thresholds
# ---------------------------------------------------------------------------

_cthr = _get("crypto.thresholds", {})

FG_EXTREME_GREED:  int   = _cthr.get("fg_extreme_greed",  80)
FG_HIGH_GREED:     int   = _cthr.get("fg_high_greed",     65)
FG_EXTREME_FEAR:   int   = _cthr.get("fg_extreme_fear",   20)
CHANGE_24H_DANGER: float = _cthr.get("change_24h_danger", -10)
CHANGE_24H_WARN:   float = _cthr.get("change_24h_warn",   -5)
CHANGE_24H_PUMP:   float = _cthr.get("change_24h_pump",   10)
CHANGE_30D_BEAR:   float = _cthr.get("change_30d_bear",   -20)
CHANGE_30D_BULL:   float = _cthr.get("change_30d_bull",   20)
ATH_DANGER_PCT:    float = _cthr.get("ath_danger_pct",    -5)
ATH_WARN_PCT:      float = _cthr.get("ath_warn_pct",      -15)
