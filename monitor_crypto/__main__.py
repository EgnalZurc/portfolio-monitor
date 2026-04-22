"""
monitor_crypto/__main__.py — Entry point: python -m monitor_crypto

This monitor tracks cryptocurrency staking positions (KuCoin Earn).
Its primary focus is showing days until each position can be redeemed,
estimated daily and accumulated staking rewards, and market signals
that may affect the decision to renew or exit a staking position.
"""
import logging
import sys
import time
from pathlib import Path

from shared.i18n import t
from shared.delivery import deliver_report
from shared.config_loader import LOG_LEVEL

from .coingecko_client import fetch_fear_greed, fetch_market_batch, fetch_ohlc
from .thresholds import POSITIONS
from .email_sender import send_email
from .report import generate_html

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

_OHLC_DELAY = 2.0  # seconds between per-coin OHLC requests (no batch endpoint)


def main() -> int:
    ids = list(dict.fromkeys(pos["coingecko_id"] for pos in POSITIONS))

    logger.warning(t("crypto.fetching_prices"))
    # Single batch call: prices + 24h change + ATH + 14d/30d changes for all coins
    market_batch = fetch_market_batch(ids)

    # Price data and market data are now unified in market_batch;
    # split into the two dicts that report.py and signals.py expect
    price_data      = {cg_id: {
        "eur":            data["eur"],
        "eur_24h_change": data["eur_24h_change"],
        "market_cap":     data["market_cap"],
    } for cg_id, data in market_batch.items()}

    market_data_map = {cg_id: {
        "ath":              data["ath"],
        "ath_change_pct":   data["ath_change_pct"],
        "price_change_14d": data["price_change_14d"],
        "price_change_30d": data["price_change_30d"],
    } for cg_id, data in market_batch.items()}

    logger.warning(t("crypto.fetching_market"))
    ohlc_map: dict = {}
    for cg_id in ids:
        if cg_id not in ohlc_map:
            ohlc_map[cg_id] = fetch_ohlc(cg_id, days=30)
            if cg_id != ids[-1]:
                time.sleep(_OHLC_DELAY)

    logger.warning(t("crypto.fetching_fg"))
    fear_greed_val, fear_greed_label = fetch_fear_greed()

    logger.warning(t("crypto.generating_html"))
    html = generate_html(
        POSITIONS, price_data, market_data_map,
        ohlc_map, fear_greed_val, fear_greed_label,
    )

    output_path = Path(__file__).parent.parent / "crypto_report.html"
    deliver_report(html, output_path, send_email)
    return 0


if __name__ == "__main__":
    sys.exit(main())
