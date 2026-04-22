"""
monitor_etf/__main__.py — Entry point: python -m monitor_etf
"""
import logging
import sys
from pathlib import Path

from shared.i18n import t
from shared.report_delivery import deliver_report

from .analysis import (
    calculate_signals, compare_vs_projection, current_phase, fetch_etf_data,
)
from .config import PORTFOLIO
from .email_sender import send_email
from .models import AlertLevel
from .report import build_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

_LEVEL_ICON = {
    AlertLevel.OK:     "✅",
    AlertLevel.INFO:   "ℹ️",
    AlertLevel.WARN:   "⚠️",
    AlertLevel.DANGER: "🚨",
}


def main() -> int:
    logger.info(t("etf.downloading"))
    results = {}

    for fund_id, cfg in PORTFOLIO.items():
        logger.info(t("etf.processing", etf_id=fund_id, ticker=cfg["ticker"]))
        try:
            hist, _ = fetch_etf_data(cfg["ticker"])
            data    = calculate_signals(hist, cfg["avg_cost"])
            results[fund_id] = (data, cfg)
            logger.info(f"    {data['price']:.2f}€  "
                        f"{_LEVEL_ICON[data['level']]} {data['level'].name}")
        except Exception as e:
            logger.error(t("etf.error_processing", etf_id=fund_id, exc=f"{type(e).__name__}: {e}"))
            continue

    if not results:
        logger.error(t("etf.no_data"))
        return 1

    logger.info(t("etf.generating_html"))
    try:
        html = build_report(results)
    except Exception as e:
        logger.error(t("etf.error_writing", exc=e))
        return 1

    output_path = Path(__file__).parent.parent / "informe_etf.html"
    deliver_report(html, output_path, send_email)

    # Print quick summary to stdout
    logger.info("\n" + "=" * 50)
    logger.info(t("etf.summary_header"))
    logger.info("=" * 50)
    for fund_id, (data, cfg) in results.items():
        logger.info(f"  {fund_id}: {data['price']:.2f}€  "
                    f"{_LEVEL_ICON[data['level']]} {data['level'].name}")
        if data["pct_vs_cost"] is not None:
            label = t("etf.summary_gain") if data["pct_vs_cost"] >= 0 else t("etf.summary_loss")
            logger.info(f"         {t('etf.summary_perf', label=label, pct=data['pct_vs_cost'])}")
        proj = compare_vs_projection(
            fund_id, data["price"], cfg["units"], cfg["avg_cost"]
        )
        if proj:
            logger.info(f"         {t('etf.summary_vs_proj', year=proj['year'], dev=proj['deviation'])}")
    logger.info(f"\n  {t('etf.summary_plan', phase=current_phase())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
