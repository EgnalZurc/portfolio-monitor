"""
monitor_crypto/report.py — HTML report generation for the crypto monitor.
"""
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional

from shared.i18n import t

from .thresholds import ATH_DANGER_PCT, ATH_WARN_PCT
from .signals import compute_signals, days_until_available


def sparkline_svg(ohlc_data: List, color: str = "#4CAF50", width: int = 120, height: int = 40) -> str:
    """Render a simple SVG sparkline from OHLC close prices."""
    if not ohlc_data or len(ohlc_data) < 2:
        return ""
    closes = [c[4] for c in ohlc_data[-30:]]
    mn, mx = min(closes), max(closes)
    if mx == mn:
        return ""
    pts = [
        f"{i / (len(closes) - 1) * width:.1f},{height - (v - mn) / (mx - mn) * height:.1f}"
        for i, v in enumerate(closes)
    ]
    return (
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.5"/>'
        f'</svg>'
    )


def _availability_badge(days_avail: int) -> str:
    """Return an HTML badge indicating when the position becomes available."""
    if days_avail == 0:
        return f'<span class="badge green">{t("crypto.available_now")}</span>'
    if days_avail <= 5:
        return f'<span class="badge orange">{t("crypto.available_rescue", days=days_avail)}</span>'
    if days_avail <= 14:
        return f'<span class="badge yellow">{t("crypto.available_in", days=days_avail)}</span>'
    return f'<span class="badge gray">{t("crypto.available_in", days=days_avail)}</span>'


def _maturity_label(pos: Dict[str, Any]) -> str:
    """Return a human-readable maturity label (fixed) or product type (flexible)."""
    if pos["type"] == "fixed":
        return t("crypto.matures", date=pos["maturity_date"])
    return t("crypto.flexible")


def _card_html(
    pos: Dict[str, Any],
    price_data: Dict[str, Any],
    market_data: Dict[str, Any],
    ohlc: List,
    fear_greed_val: Optional[int],
) -> str:
    """Render the HTML card for a single staking position."""
    cg_id      = pos["coingecko_id"]
    price      = price_data.get(cg_id, {}).get("eur", 0)
    change_24h = price_data.get(cg_id, {}).get("eur_24h_change", 0)
    value_eur  = pos["amount"] * price
    days_avail = days_until_available(pos)
    ath_pct    = market_data.get("ath_change_pct")
    change_30d = market_data.get("price_change_30d")
    change_14d = market_data.get("price_change_14d")

    # Staking earnings
    daily_gain_token = pos["amount"] * (pos["apy"] / 100) / 365
    daily_gain_eur   = daily_gain_token * price
    start            = datetime.fromisoformat(pos["start_date"]).replace(tzinfo=timezone.utc)
    days_staked      = max(1, (datetime.now(timezone.utc) - start).days)
    total_earned_eur = daily_gain_token * days_staked * price

    c24 = "#27ae60" if change_24h >= 0 else "#c0392b"
    c30 = "#27ae60" if (change_30d or 0) >= 0 else "#c0392b"
    c14 = "#27ae60" if (change_14d or 0) >= 0 else "#c0392b"

    spark        = sparkline_svg(ohlc, color=c24)
    avail_badge  = _availability_badge(days_avail)
    maturity_str = _maturity_label(pos)

    # Signal rows
    _css_map     = {"danger": "signal-danger", "warning": "signal-warning", "success": "signal-ok"}
    pos_signals  = compute_signals(pos, price_data, market_data, fear_greed_val)
    signals_html = "".join(
        f'<div class="{_css_map.get(stype, "signal-ok")}">{msg}</div>'
        for stype, msg in pos_signals
    ) or f'<div class="signal-ok">{t("crypto.no_alerts")}</div>'

    change_30d_str = f"{change_30d:+.1f}%" if change_30d is not None else "N/A"
    change_14d_str = f"{change_14d:+.1f}%" if change_14d is not None else "N/A"
    if ath_pct is not None:
        ath_color = "#c0392b" if ath_pct >= ATH_DANGER_PCT else ("#e67e22" if ath_pct >= ATH_WARN_PCT else "#888")
        ath_html  = f'<span style="color:{ath_color}">ATH: {ath_pct:.1f}%</span>'
    else:
        ath_html = ""

    return (
        f'<div class="card">'
        f'<div class="card-header">'
        f'<div><span class="symbol">{pos["symbol"]}</span>'
        f'<span class="name">{pos["name"]}</span>{avail_badge}</div>'
        f'<div class="price-block"><span class="price">€{price:,.2f}</span>'
        f'<span style="color:{c24}">{change_24h:+.2f}% 24h</span></div></div>'
        f'<div class="card-body"><div class="col-data">'
        f'<div class="row-data"><span>{t("crypto.label_amount")}</span> <strong>{pos["amount"]:.6f} {pos["symbol"]}</strong></div>'
        f'<div class="row-data"><span>{t("crypto.label_value")}</span> <strong>€{value_eur:,.2f}</strong></div>'
        f'<div class="row-data"><span>{t("crypto.label_product")}</span> <strong>{pos["product"]} ({pos["apy"]}% APY)</strong></div>'
        f'<div class="row-data"><span>{maturity_str}</span></div>'
        f'<div class="row-data"><span>{t("crypto.label_daily_gain")}</span> <strong>+{daily_gain_token:.8f} {pos["symbol"]} (≈€{daily_gain_eur:.4f})</strong></div>'
        f'<div class="row-data"><span>{t("crypto.label_accumulated")}</span> <strong>+€{total_earned_eur:.4f} {t("crypto.label_accumulated_since", date=pos["start_date"])}</strong></div>'
        f'<div class="row-data">{ath_html} &nbsp; '
        f'<span style="color:{c30}">30d: {change_30d_str}</span> &nbsp; '
        f'<span style="color:{c14}">14d: {change_14d_str}</span></div>'
        f'</div><div class="col-spark">{spark}'
        f'<span style="font-size:10px;color:#555;margin-top:4px">{t("crypto.ui.sparkline_period")}</span></div></div>'
        f'<div class="signals">{signals_html}</div></div>'
    )


_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f1117; color: #e0e0e0; }
.container { max-width: 860px; margin: 0 auto; padding: 20px; }
.header { background: #1a1d27; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; border-left: 5px solid VAR_COLOR; }
.header h1 { font-size: 20px; color: #fff; }
.header .total { font-size: 32px; font-weight: bold; color: #fff; margin: 6px 0; }
.header .date { font-size: 12px; color: #888; }
.status-banner { padding: 14px 20px; border-radius: 10px; font-size: 16px; font-weight: bold; margin-bottom: 16px; text-align: center; }
.status-banner.danger  { background: #3d1010; color: #ff6b6b; border: 2px solid #c0392b; }
.status-banner.warning { background: #2d2010; color: #f39c12; border: 2px solid #e67e22; }
.status-banner.ok      { background: #0d2d14; color: #2ecc71; border: 2px solid #27ae60; }
.fg-box { display: inline-flex; align-items: center; gap: 10px; border: 2px solid; border-radius: 10px; padding: 10px 16px; margin-bottom: 16px; background: #1a1d27; }
.card { background: #1a1d27; border-radius: 12px; padding: 18px; margin-bottom: 14px; border: 1px solid #2a2d3a; }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.symbol { font-size: 22px; font-weight: bold; color: #fff; margin-right: 8px; }
.name { font-size: 14px; color: #888; }
.price-block { text-align: right; }
.price { font-size: 20px; font-weight: bold; color: #fff; display: block; }
.card-body { display: flex; justify-content: space-between; gap: 16px; }
.col-data { flex: 1; }
.col-spark { display: flex; flex-direction: column; align-items: flex-end; }
.row-data { font-size: 13px; margin-bottom: 5px; display: flex; gap: 6px; }
.row-data span { color: #888; }
.row-data strong { color: #e0e0e0; }
.signals { margin-top: 12px; border-top: 1px solid #2a2d3a; padding-top: 10px; display: flex; flex-direction: column; gap: 5px; }
.signal-danger  { background: #2d0f0f; color: #ff6b6b; border-radius: 6px; padding: 6px 10px; font-size: 13px; }
.signal-warning { background: #2d1f0f; color: #f39c12; border-radius: 6px; padding: 6px 10px; font-size: 13px; }
.signal-ok      { background: #0d2010; color: #2ecc71; border-radius: 6px; padding: 6px 10px; font-size: 13px; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 20px; margin-left: 6px; font-weight: bold; }
.badge.green  { background: #0d3d1a; color: #2ecc71; }
.badge.orange { background: #3d1f0a; color: #e67e22; }
.badge.yellow { background: #3d330a; color: #f1c40f; }
.badge.gray   { background: #252830; color: #888; }
.footer { text-align: center; margin-top: 24px; padding-bottom: 20px; }
.btn { display: inline-block; background: #2980b9; color: #fff; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-size: 16px; font-weight: bold; }
.footer-note { margin-top: 10px; font-size: 12px; color: #555; }
"""


def generate_html(
    positions: List[Dict[str, Any]],
    price_data: Dict[str, Any],
    market_data_map: Dict[str, Any],
    ohlc_map: Dict[str, Any],
    fear_greed_val: Optional[int],
    fear_greed_label: Optional[str],
) -> str:
    """Render the full HTML report for all crypto positions."""
    today     = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
    total_eur = sum(
        pos["amount"] * price_data.get(pos["coingecko_id"], {}).get("eur", 0)
        for pos in positions
    )
    sorted_pos = sorted(positions, key=days_until_available)

    # Determine overall alert status
    all_signals = [
        s for pos in sorted_pos
        for s in compute_signals(pos, price_data, market_data_map.get(pos["coingecko_id"], {}), fear_greed_val)
    ]
    has_danger  = any(s[0] == "danger"  for s in all_signals)
    has_warning = any(s[0] == "warning" for s in all_signals)

    if has_danger:
        header_color  = "#c0392b"
        header_icon   = "⚠️"
        status_class  = "danger"
        status_text   = t("crypto.status_danger")
    elif has_warning:
        header_color  = "#e67e22"
        header_icon   = "🔔"
        status_class  = "warning"
        status_text   = t("crypto.status_warning")
    else:
        header_color  = "#27ae60"
        header_icon   = "✅"
        status_class  = "ok"
        status_text   = t("crypto.status_ok")

    status_banner = f'<div class="status-banner {status_class}">{status_text}</div>'
    cards_html    = "".join(
        _card_html(pos, price_data, market_data_map.get(pos["coingecko_id"], {}),
                   ohlc_map.get(pos["coingecko_id"], []), fear_greed_val)
        for pos in sorted_pos
    )

    fg_color = "#27ae60" if (fear_greed_val or 50) < 40 else ("#e67e22" if (fear_greed_val or 50) < 65 else "#c0392b")
    fg_html  = (
        f'<div class="fg-box" style="border-color:{fg_color};color:{fg_color}">'
        f'<span style="font-size:28px;font-weight:bold">{fear_greed_val or "?"}</span>'
        f'<div><strong>Fear &amp; Greed</strong><br>{fear_greed_label or "N/A"}</div></div>'
    ) if fear_greed_val else ""

    css = _CSS.replace("VAR_COLOR", header_color)

    return f"""<!DOCTYPE html>
<html lang="{os.environ.get('MONITOR_LANG', 'es')}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t("crypto.report_title")} — {today}</title>
<style>{css}</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{header_icon} {t("crypto.report_title")}</h1>
    <div class="total">€{total_eur:,.2f} EUR</div>
    <div class="date">{t("crypto.report_subtitle", date=today)}</div>
  </div>
  {status_banner}
  {fg_html}
  {cards_html}
  <div class="footer">
    <a href="https://www.kucoin.com/es/assets/earn-account" class="btn">{t("crypto.ui.kucoin_btn")}</a>
    <div class="footer-note">{t("crypto.footer_note")}</div>
  </div>
</div>
</body>
</html>"""
