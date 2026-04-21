"""
monitor_crypto/api.py — External API calls (CoinGecko, Fear & Greed).
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

from shared.i18n import t

logger   = logging.getLogger(__name__)
_TIMEOUT = 10


def get_prices(coingecko_ids: List[str]) -> Dict[str, Any]:
    """Fetch EUR prices, 24h and 7d changes for a list of CoinGecko IDs."""
    ids = ",".join(set(coingecko_ids))
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=eur"
        f"&include_24hr_change=true&include_7d_change=true&include_market_cap=true"
    )
    try:
        r = requests.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(t("crypto.error_prices", exc=e))
        return {}


def get_ohlc(coingecko_id: str, days: int = 30) -> List:
    """Fetch OHLC data used to render the sparkline chart."""
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coingecko_id}"
        f"/ohlc?vs_currency=eur&days={days}"
    )
    try:
        r = requests.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(t("crypto.error_ohlc", cg_id=coingecko_id, exc=e))
        return []


def get_market_data(coingecko_id: str) -> Dict[str, Any]:
    """Fetch extended market data: ATH, 14d and 30d price changes."""
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coingecko_id}"
        f"?localization=false&tickers=false&community_data=false&developer_data=false"
    )
    try:
        r  = requests.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        md = r.json().get("market_data", {})
        return {
            "ath":             md.get("ath", {}).get("eur"),
            "ath_change_pct":  md.get("ath_change_percentage", {}).get("eur"),
            "price_change_30d": md.get("price_change_percentage_30d"),
            "price_change_14d": md.get("price_change_percentage_14d"),
        }
    except Exception as e:
        logger.error(t("crypto.error_market", cg_id=coingecko_id, exc=e))
        return {}


def get_fear_greed() -> Tuple[Optional[int], Optional[str]]:
    """Fetch the current Fear & Greed index value and label."""
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return int(data["data"][0]["value"]), data["data"][0]["value_classification"]
    except Exception as e:
        logger.error(t("crypto.error_fg", exc=e))
        return None, None
