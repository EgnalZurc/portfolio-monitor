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
from shared.report_delivery import deliver_report
from shared.settings import LOG_LEVEL

from .api import get_fear_greed, get_market_data, get_ohlc, get_prices
from .config import POSITIONS
from .email_sender import send_email
from .report import generate_html

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

_API_DELAY = 1.5  # seconds between CoinGecko requests (free tier rate limit)


def main() -> int:
    logger.warning(t("crypto.fetching_prices"))
    ids        = [pos["coingecko_id"] for pos in POSITIONS]
    price_data = get_prices(ids)

    logger.warning(t("crypto.fetching_market"))
    market_data_map: dict = {}
    ohlc_map: dict        = {}
    for pos in POSITIONS:
        cg_id = pos["coingecko_id"]
        if cg_id not in market_data_map:
            time.sleep(_API_DELAY)
            market_data_map[cg_id] = get_market_data(cg_id)
            time.sleep(_API_DELAY)
            ohlc_map[cg_id]        = get_ohlc(cg_id, days=30)

    logger.warning(t("crypto.fetching_fg"))
    fear_greed_val, fear_greed_label = get_fear_greed()

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
