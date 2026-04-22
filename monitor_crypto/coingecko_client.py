"""
monitor_crypto/coingecko_client.py — CoinGecko API client.

Uses /coins/markets to fetch prices, 24h change, ATH and 14d/30d changes
for all positions in a single request. OHLC is fetched per-coin (no batch
endpoint available) with exponential backoff retry on 429.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from shared.i18n import t

logger    = logging.getLogger(__name__)
_TIMEOUT  = 10
_RETRIES  = 4
_BACKOFF  = 2.0  # seconds; doubles on each retry: 2, 4, 8, 16

_MARKETS_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=eur&ids={ids}&price_change_percentage=14d,30d"
)
_OHLC_URL    = "https://api.coingecko.com/api/v3/coins/{id}/ohlc?vs_currency=eur&days={days}"
_FG_URL      = "https://api.alternative.me/fng/?limit=1"


def _get(url: str) -> requests.Response:
    """GET with exponential backoff retry on 429."""
    delay = _BACKOFF
    for attempt in range(1, _RETRIES + 1):
        r = requests.get(url, timeout=_TIMEOUT)
        if r.status_code == 429:
            logger.debug(f"Rate limited, retrying in {delay:.0f}s (attempt {attempt}/{_RETRIES})")
            time.sleep(delay)
            delay *= 2
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r  # unreachable; satisfies type checker


def fetch_market_batch(coingecko_ids: List[str]) -> Dict[str, Any]:
    """
    Fetch price, 24h change, ATH, 14d and 30d changes for all coins
    in a single /coins/markets request.

    Returns a dict keyed by coingecko_id with normalised fields.
    """
    ids = ",".join(dict.fromkeys(coingecko_ids))  # deduplicate, preserve order
    try:
        rows = _get(_MARKETS_URL.format(ids=ids)).json()
        return {
            row["id"]: {
                "eur":             row.get("current_price", 0),
                "eur_24h_change":  row.get("price_change_percentage_24h", 0),
                "market_cap":      row.get("market_cap"),
                "ath":             row.get("ath"),
                "ath_change_pct":  row.get("ath_change_percentage"),
                "price_change_14d": row.get("price_change_percentage_14d_in_currency"),
                "price_change_30d": row.get("price_change_percentage_30d_in_currency"),
            }
            for row in rows
        }
    except Exception as e:
        logger.error(t("crypto.error_prices", exc=e))
        return {}


def fetch_ohlc(coingecko_id: str, days: int = 30) -> List:
    """Fetch OHLC data used to render the sparkline chart."""
    try:
        return _get(_OHLC_URL.format(id=coingecko_id, days=days)).json()
    except Exception as e:
        logger.error(t("crypto.error_ohlc", cg_id=coingecko_id, exc=e))
        return []


def fetch_fear_greed() -> Tuple[Optional[int], Optional[str]]:
    """Fetch the current Fear & Greed index value and label."""
    try:
        r = requests.get(_FG_URL, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return int(data["data"][0]["value"]), data["data"][0]["value_classification"]
    except Exception as e:
        logger.error(t("crypto.error_fg", exc=e))
        return None, None
