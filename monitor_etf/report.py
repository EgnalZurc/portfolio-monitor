"""
monitor_etf/report.py — HTML report generation.
"""
import html as _html
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from shared.i18n import t
from shared.utils import fmt_fecha_madrid

from .analysis import (
    compare_vs_projection, current_contribution, current_phase,
    recommendation, years_since_start,
)
from .config import PLAN
from .fiscal import calculate_tax_impact
from .models import AlertLevel


# ---------------------------------------------------------------------------
# HTML block helpers
# ---------------------------------------------------------------------------

def _tax_block(tax: Optional[Dict[str, float]]) -> str:
    """Render the 'sell today' tax impact block."""
    if not tax:
        return ""
    color = "#1A7A4A" if tax["gain"] >= 0 else "#C0392B"
    bg    = "#E8F5E9" if tax["gain"] >= 0 else "#FDECEA"
    sign  = "+" if tax["gain"] >= 0 else ""
    return (
        f'<div style="background:{bg};border-radius:8px;padding:16px;margin-top:12px;border-left:4px solid {color}">'
        f'<h4 style="margin:0 0 10px;color:#1B2A4A;font-size:13px;text-transform:uppercase">{t("etf.ui.tax_title")}</h4>'
        f'<table style="width:100%;font-size:13px;border-collapse:collapse">'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.tax_gross")}</td>'
        f'<td style="text-align:right;font-weight:600;color:{color}">{sign}{tax["gain"]:,.0f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.tax_irpf")}</td>'
        f'<td style="text-align:right;font-weight:600;color:#C0392B">−{tax["tax"]:,.0f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0"><strong>{t("etf.ui.tax_net")}</strong></td>'
        f'<td style="text-align:right;font-weight:700;color:{color}">{tax["net"]:,.0f} €</td></tr>'
        f'</table>'
        f'<p style="margin:10px 0 0;font-size:12px;color:#666">'
        f'{t("etf.ui.tax_set_aside", amount=tax["set_aside"])}</p></div>'
    )


def _projection_block(proj: Optional[Dict[str, Any]], accent: str) -> str:
    """Render the plan projection tracking block."""
    if not proj:
        return ""
    dev   = proj["deviation"]
    year  = int(proj["year"])
    color = "#1A7A4A" if dev >= 0 else "#C0392B"
    bg    = "#E8F5E9" if dev >= 0 else "#FFF3CD"
    emoji = "🚀" if dev > 0.10 else ("✅" if dev >= -0.10 else "⚠️")
    sign  = "+" if dev >= 0 else ""
    return (
        f'<div style="background:{bg};border-radius:8px;padding:16px;margin-top:12px;border-left:4px solid {accent}">'
        f'<h4 style="margin:0 0 10px;color:#1B2A4A;font-size:13px;text-transform:uppercase">{t("etf.ui.proj_title", year=year)}</h4>'
        f'<table style="width:100%;font-size:13px;border-collapse:collapse">'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.proj_expected", year=year)}</td>'
        f'<td style="text-align:right;font-weight:600">{proj["expected"]:,.0f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.proj_actual")}</td>'
        f'<td style="text-align:right;font-weight:600">{proj["actual"]:,.0f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0"><strong>{t("etf.ui.proj_deviation")}</strong></td>'
        f'<td style="text-align:right;font-weight:700;color:{color}">{emoji} {sign}{dev:.1%}</td></tr>'
        f'</table></div>'
    )


def _signals_block(signals: List[Tuple[str, str, str]]) -> str:
    """Render the list of detected signals."""
    parts = []
    for title, body, level_key in signals:
        lvl = AlertLevel[level_key]
        parts.append(
            f'<div style="margin:8px 0;padding:10px 14px;border-radius:8px;'
            f'background:{lvl.background};border-left:4px solid {lvl.color}">'
            f'<strong style="color:{lvl.color}">{_html.escape(title)}</strong><br>'
            f'<span style="font-size:13px;color:#444">{_html.escape(body)}</span></div>'
        )
    return "".join(parts)


def _status_card(
    fund_id: str, cfg: Dict, data: Dict,
    fmt_pct: Callable, color_fn: Callable,
) -> str:
    """Render the compact status card for a fund."""
    level         = data["level"]
    portfolio_val = data["price"] * cfg["units"]
    gain_eur      = (portfolio_val - cfg["units"] * cfg["avg_cost"]) \
                    if cfg["avg_cost"] and cfg["units"] > 0 else 0
    gain_pct      = data["pct_vs_cost"] if data["pct_vs_cost"] is not None else 0
    rec_title, _, rec_color = recommendation(level, cfg["name"])
    return (
        f'<div style="flex:1;min-width:280px;background:#fff;border-radius:12px;padding:24px;'
        f'box-shadow:0 2px 12px rgba(0,0,0,0.08);border-top:5px solid {cfg["color"]}">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">'
        f'<div><h2 style="margin:0;color:#1B2A4A;font-size:20px">{_html.escape(fund_id)}</h2>'
        f'<p style="margin:3px 0 0;color:#888;font-size:12px">{_html.escape(cfg["isin"])}</p></div>'
        f'<div style="font-size:18px">{level.emoji}</div>'
        f'<div style="font-size:11px;font-weight:700;color:{level.color}">{level.label}</div></div></div>'
        f'<div style="font-size:30px;font-weight:700;color:#1B2A4A;margin-bottom:4px">{data["price"]:.2f} €</div>'
        f'<div style="font-size:13px;color:{color_fn(data["chg_1d"])};font-weight:600;margin-bottom:16px">'
        f'{t("etf.ui.today", pct=fmt_pct(data["chg_1d"]))} &nbsp;·&nbsp;'
        f'<span style="color:{color_fn(data["chg_ytd"])}">{fmt_pct(data["chg_ytd"])} YTD</span></div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px">'
        f'<div style="background:#F5F8FF;border-radius:6px;padding:10px">'
        f'<div style="font-size:10px;color:#888;text-transform:uppercase">{t("etf.ui.portfolio_value")}</div>'
        f'<div style="font-size:15px;font-weight:700;color:#1B2A4A">{portfolio_val:,.0f} €</div></div>'
        f'<div style="background:#F5F8FF;border-radius:6px;padding:10px">'
        f'<div style="font-size:10px;color:#888;text-transform:uppercase">{t("etf.ui.gain_loss")}</div>'
        f'<div style="font-size:15px;font-weight:700;color:{color_fn(gain_eur)}">'
        f'{gain_eur:+,.0f} € ({fmt_pct(gain_pct)})</div></div></div>'
        f'<div style="padding:10px 14px;border-radius:8px;background:{level.background};border-left:3px solid {rec_color}">'
        f'<strong style="font-size:12px;color:{rec_color}">{_html.escape(rec_title)}</strong></div></div>'
    )


def _detail_card(
    fund_id: str, cfg: Dict, data: Dict,
    fmt_pct: Callable, color_fn: Callable,
) -> str:
    """Render the full detail card for a fund."""
    level         = data["level"]
    ma50_str      = f"{data['ma50']:.2f} €"  if data["ma50"]  else "—"
    ma200_str     = f"{data['ma200']:.2f} €" if data["ma200"] else "—"
    portfolio_val = data["price"] * cfg["units"]
    gain_eur      = (portfolio_val - cfg["units"] * cfg["avg_cost"]) \
                    if cfg["avg_cost"] and cfg["units"] > 0 else 0
    gain_pct      = data["pct_vs_cost"] if data["pct_vs_cost"] is not None else 0
    avg_cost_str  = f"{cfg['avg_cost']:.2f} €" if cfg["avg_cost"] else "—"
    rec_title, rec_body, rec_color = recommendation(level, cfg["name"])

    tax  = calculate_tax_impact(cfg["units"], cfg["avg_cost"], data["price"])
    proj = compare_vs_projection(fund_id, data["price"], cfg["units"], cfg["avg_cost"])

    changes = "".join(
        f'<div style="background:#F5F8FF;border-radius:8px;padding:10px;text-align:center">'
        f'<div style="font-size:10px;color:#888;text-transform:uppercase">{label}</div>'
        f'<div style="font-size:14px;font-weight:700;color:{color_fn(val) if isinstance(val, float) and abs(val) < 2 else cfg["color"]}">'
        f'{fmt_val}</div></div>'
        for label, val, fmt_val in [
            (t("etf.ui.chg_1d"),  data["chg_1d"],  fmt_pct(data["chg_1d"])),
            (t("etf.ui.chg_1m"),  data["chg_1m"],  fmt_pct(data["chg_1m"])),
            (t("etf.ui.chg_3m"),  data["chg_3m"],  fmt_pct(data["chg_3m"])),
            (t("etf.ui.chg_ytd"), data["chg_ytd"], fmt_pct(data["chg_ytd"])),
        ]
    )
    return (
        f'<div style="background:#fff;border-radius:12px;padding:28px;margin-bottom:20px;'
        f'box-shadow:0 2px 12px rgba(0,0,0,0.08);border-left:5px solid {cfg["color"]}">'
        f'<h3 style="margin:0 0 4px;color:#1B2A4A;font-size:18px">'
        f'{_html.escape(fund_id)} — {_html.escape(cfg["name"])}</h3>'
        f'<p style="margin:0 0 20px;color:#888;font-size:12px">{_html.escape(cfg["isin"])} · TER 0,15%</p>'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px">{changes}</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">'
        f'<div style="background:#F5F8FF;border-radius:8px;padding:14px">'
        f'<h4 style="margin:0 0 10px;color:#1B2A4A;font-size:12px;text-transform:uppercase">{t("etf.ui.technical")}</h4>'
        f'<table style="width:100%;font-size:13px;border-collapse:collapse">'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.high_52w")}</td><td style="text-align:right;font-weight:600">{data["high_52w"]:.2f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.low_52w")}</td><td style="text-align:right;font-weight:600">{data["low_52w"]:.2f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.ma50")}</td><td style="text-align:right;font-weight:600">{ma50_str}</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.ma200")}</td><td style="text-align:right;font-weight:600">{ma200_str}</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.annual_vol")}</td><td style="text-align:right;font-weight:600">{data["annual_vol"]:.1%}</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.drawdown")}</td>'
        f'<td style="text-align:right;font-weight:600;color:{color_fn(data["drawdown"])}">{fmt_pct(data["drawdown"])}</td></tr>'
        f'</table></div>'
        f'<div style="background:#F5F8FF;border-radius:8px;padding:14px">'
        f'<h4 style="margin:0 0 10px;color:#1B2A4A;font-size:12px;text-transform:uppercase">{t("etf.ui.position")}</h4>'
        f'<table style="width:100%;font-size:13px;border-collapse:collapse">'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.units")}</td><td style="text-align:right;font-weight:600">{cfg["units"]:.4f}</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.avg_cost")}</td><td style="text-align:right;font-weight:600">{avg_cost_str}</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.current_value")}</td><td style="text-align:right;font-weight:600">{portfolio_val:,.2f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.gain_eur")}</td>'
        f'<td style="text-align:right;font-weight:600;color:{color_fn(gain_eur)}">{gain_eur:+,.2f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.gain_pct")}</td>'
        f'<td style="text-align:right;font-weight:600;color:{color_fn(gain_pct)}">{fmt_pct(gain_pct)}</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.monthly_contrib")}</td>'
        f'<td style="text-align:right;font-weight:600">{t("etf.ui.contrib_amount", amount=current_contribution(fund_id))}</td></tr>'
        f'</table></div></div>'
        f'{_projection_block(proj, cfg["color"])}'
        f'{_tax_block(tax)}'
        f'<h4 style="margin:20px 0 10px;color:#1B2A4A;font-size:12px;text-transform:uppercase">{t("etf.ui.signals_header")}</h4>'
        f'{_signals_block(data["signals"])}'
        f'<div style="margin-top:14px;padding:14px;border-radius:8px;background:{level.background};border:2px solid {rec_color}">'
        f'<strong style="color:{rec_color};font-size:14px">{_html.escape(rec_title)}</strong><br>'
        f'<p style="margin:6px 0 0;color:#333;font-size:13px;line-height:1.6">{_html.escape(rec_body)}</p>'
        f'</div></div>'
    )


# ---------------------------------------------------------------------------
# Main report builder
# ---------------------------------------------------------------------------

def build_report(results: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]]) -> str:
    """Render the full ETF HTML report."""
    timestamp = fmt_fecha_madrid()
    fmt_pct   = lambda v: f"+{v:.2%}" if v >= 0 else f"{v:.2%}"
    color_fn  = lambda v: "#1A7A4A" if v >= 0 else "#C0392B"

    # Total portfolio value block
    total      = 0.0
    fund_rows  = []
    for fund_id, (data, cfg) in results.items():
        val    = data["price"] * cfg["participaciones"]
        total += val
        fund_rows.append((fund_id, val))

    fund_rows_html = "".join(
        f'<div style="color:#8EA8C8"><span style="color:white;font-weight:600">'
        f'{_html.escape(fid)}</span><br>{v:,.0f} €</div>'
        for fid, v in fund_rows
    )
    total_block = (
        f'<div style="background:linear-gradient(135deg,#1B2A4A 0%,#2C3E50 100%);'
        f'border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 4px 12px rgba(0,0,0,0.15)">'
        f'<p style="color:#8EA8C8;font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px">{t("etf.ui.total_title")}</p>'
        f'<div style="font-size:48px;font-weight:800;color:white;margin:0">{total:,.0f} €</div>'
        f'<p style="color:#8EA8C8;font-size:12px;margin:8px 0 0">{t("etf.ui.updated", ts=_html.escape(timestamp))}</p>'
        f'<div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.1);'
        f'display:grid;grid-template-columns:repeat({min(len(fund_rows),2)},1fr);gap:12px;font-size:12px">'
        f'{fund_rows_html}</div></div>'
    )

    # Status overview block
    status_cards = "".join(
        _status_card(fid, cfg, data, fmt_pct, color_fn)
        for fid, (data, cfg) in results.items()
    )
    status_block = (
        f'<div style="background:#1B2A4A;border-radius:12px;padding:20px 24px;margin-bottom:8px">'
        f'<h2 style="color:white;font-size:16px;margin:0;text-transform:uppercase;letter-spacing:1px">'
        f'{t("etf.ui.status_header")}</h2>'
        f'<p style="color:#8EA8C8;font-size:13px;margin:4px 0 0">{timestamp}</p></div>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:32px">{status_cards}</div>'
    )

    # Detailed analysis block
    detail_cards = "".join(
        _detail_card(fid, cfg, data, fmt_pct, color_fn)
        for fid, (data, cfg) in results.items()
    )
    detail_block = (
        f'<div style="background:#1B2A4A;border-radius:12px;padding:20px 24px;margin-bottom:8px">'
        f'<h2 style="color:white;font-size:16px;margin:0;text-transform:uppercase;letter-spacing:1px">'
        f'{t("etf.ui.detail_header")}</h2></div>{detail_cards}'
    )

    # Investment plan block
    today       = datetime.today()
    is_phase2   = today >= PLAN["fecha_cambio_fase"]
    months_left = max(0, int((PLAN["fecha_cambio_fase"] - today).days / 30.44))
    phase2_date = PLAN["fecha_cambio_fase"].strftime("%B %Y")
    year_num    = years_since_start()
    total_val   = sum(d["price"] * c["units"] for d, c in results.values())
    total_gain  = sum(
        d["price"] * c["units"] - c["units"] * c["avg_cost"]
        for d, c in results.values()
        if c["avg_cost"] and c["units"] > 0
    )
    milestone_total = sum(
        PLAN["hitos"].get(min(year_num, 10), (0, 0))[i]
        for i in range(len(results))
    )

    if is_phase2:
        phase_block = (
            f'<div style="background:#E8F5E9;border-radius:8px;padding:16px;border-left:4px solid #1A7A4A;margin-bottom:12px">'
            f'<strong style="color:#1A7A4A;font-size:15px">{t("etf.ui.phase2_active")}</strong>'
            f'<p style="margin:8px 0 0;font-size:13px;color:#333">{t("etf.ui.phase2_body")}</p></div>'
        )
    else:
        bar = max(5, min(100, int((1 - months_left / 36) * 100)))
        phase_block = (
            f'<div style="background:#FFF3CD;border-radius:8px;padding:16px;border-left:4px solid #F0A500;margin-bottom:12px">'
            f'<strong style="color:#856404;font-size:15px">{t("etf.ui.phase1_active")}</strong>'
            f'<p style="margin:8px 0 0;font-size:13px;color:#333">{t("etf.ui.phase1_body", months=months_left, date=phase2_date)}</p>'
            f'<div style="margin-top:12px;background:#E0E0E0;border-radius:99px;height:10px">'
            f'<div style="background:#F0A500;width:{bar}%;height:10px;border-radius:99px"></div></div></div>'
        )

    contributions = "".join(
        f'<tr><td style="color:#666;padding:3px 0">{fid}</td>'
        f'<td style="text-align:right;font-weight:700">{t("etf.ui.contrib_amount", amount=current_contribution(fid))}</td></tr>'
        for fid in results
    )
    plan_block = (
        f'<div style="background:#1B2A4A;border-radius:12px;padding:20px 24px;margin-bottom:8px">'
        f'<h2 style="color:white;font-size:16px;margin:0;text-transform:uppercase;letter-spacing:1px">'
        f'{t("etf.ui.plan_header")}</h2></div>'
        f'<div style="background:#fff;border-radius:12px;padding:28px;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">'
        f'{phase_block}'
        f'<div style="background:#F5F8FF;border-radius:8px;padding:14px;margin-top:12px">'
        f'<h4 style="margin:0 0 10px;font-size:12px;text-transform:uppercase;color:#1B2A4A">{t("etf.ui.milestone_header", year=min(year_num,10))}</h4>'
        f'<table style="width:100%;font-size:13px;border-collapse:collapse">'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.milestone_expected")}</td><td style="text-align:right;font-weight:700">{milestone_total:,.0f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.milestone_actual")}</td><td style="text-align:right;font-weight:700">{total_val:,.0f} €</td></tr>'
        f'<tr><td style="color:#666;padding:3px 0">{t("etf.ui.milestone_gain")}</td>'
        f'<td style="text-align:right;font-weight:700;color:{color_fn(total_gain)}">{total_gain:+,.0f} €</td></tr>'
        f'</table></div>'
        f'<div style="margin-top:12px;background:#F5F8FF;border-radius:8px;padding:14px">'
        f'<h4 style="margin:0 0 10px;font-size:12px;text-transform:uppercase;color:#1B2A4A">{t("etf.ui.contrib_header")}</h4>'
        f'<table style="width:100%;font-size:13px;border-collapse:collapse">{contributions}</table></div></div>'
    )

    disclaimer = (
        f'<div style="background:#FFF3CD;border-radius:10px;padding:16px 20px;margin-top:4px;border-left:4px solid #F0A500">'
        f'<strong style="color:#856404;font-size:12px">{t("etf.ui.disclaimer_title")}</strong>'
        f'<p style="margin:6px 0 0;font-size:12px;color:#444;line-height:1.6">{t("etf.ui.disclaimer_body")}</p></div>'
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t("etf.ui.report_title")} — {timestamp}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #EEF3FA; color: #1B2A4A; }}
        code {{ background:#eee; padding:1px 5px; border-radius:3px; font-size:12px; }}
    </style>
</head>
<body>
<div style="max-width:900px;margin:0 auto;padding:24px 16px">
    <div style="background:#1B2A4A;border-radius:12px;padding:24px 28px;margin-bottom:24px;color:white;
                display:flex;justify-content:space-between;align-items:center">
        <div>
            <h1 style="font-size:22px;margin-bottom:4px">{t("etf.ui.report_title")}</h1>
            <p style="color:#8EA8C8;font-size:13px">{current_phase()}</p>
        </div>
        <div style="text-align:right;color:#8EA8C8;font-size:12px">{timestamp}</div>
    </div>
    {total_block}
    {status_block}
    {detail_block}
    {plan_block}
    {disclaimer}
    <p style="text-align:center;color:#aaa;font-size:11px;margin-top:16px">monitor_etf</p>
</div>
</body>
</html>"""
