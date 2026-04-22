"""
shared/i18n.py — Internationalisation support (es / en).

Usage:
    from shared.i18n import t
    logger.info(t("etf.downloading"))
    senales.append((t("signal.mm200.title"), t("signal.mm200.body", price=p, mm=m), "WARN"))

Language is resolved from (in order of priority):
    1. MONITOR_LANG environment variable
    2. LANG key in the monitor's config module
    3. Default: "es"
"""
import os
from typing import Any

# ---------------------------------------------------------------------------
# Translation catalogue
# ---------------------------------------------------------------------------
_CATALOGUE: dict[str, dict[str, str]] = {
    # ── ETF monitor — __main__ ──────────────────────────────────────────────
    "etf.downloading":          {"es": "📊 Descargando datos de mercado...",
                                 "en": "📊 Downloading market data..."},
    "etf.processing":           {"es": "  → {etf_id} ({ticker})...",
                                 "en": "  → {etf_id} ({ticker})..."},
    "etf.error_processing":     {"es": "Error procesando {etf_id}: {exc}",
                                 "en": "Error processing {etf_id}: {exc}"},
    "etf.no_data":              {"es": "❌ No se pudieron obtener datos. Comprueba tu conexión.",
                                 "en": "❌ Could not retrieve data. Check your connection."},
    "etf.generating_html":      {"es": "📝 Generando informe HTML...",
                                 "en": "📝 Generating HTML report..."},
    "etf.report_generated":     {"es": "✅ Informe generado: {path}",
                                 "en": "✅ Report generated: {path}"},
    "etf.error_writing":        {"es": "Error escribiendo HTML: {exc}",
                                 "en": "Error writing HTML: {exc}"},
    "etf.opening_browser":      {"es": "🌐 Abriendo en el navegador...",
                                 "en": "🌐 Opening in browser..."},
    "etf.summary_header":       {"es": "RESUMEN RÁPIDO",
                                 "en": "QUICK SUMMARY"},
    "etf.summary_gain":         {"es": "ganancia",
                                 "en": "gain"},
    "etf.summary_loss":         {"es": "pérdida",
                                 "en": "loss"},
    "etf.summary_vs_proj":      {"es": "vs proyección año {year}: {dev:+.1%}",
                                 "en": "vs projection year {year}: {dev:+.1%}"},
    "etf.summary_plan":         {"es": "Plan actual: {phase}",
                                 "en": "Current plan: {phase}"},
    "etf.summary_perf":         {"es": "{label}: {pct:+.2%} sobre precio medio",
                                 "en": "{label}: {pct:+.2%} vs average cost"},

    # ── ETF monitor — analysis ──────────────────────────────────────────────
    "etf.hist_empty":           {"es": "Historial vacío para {ticker}",
                                 "en": "Empty history for {ticker}"},
    "etf.hist_insufficient":    {"es": "Historial insuficiente para análisis",
                                 "en": "Insufficient history for analysis"},
    "etf.error_years":          {"es": "Error al calcular años desde inicio: {exc}",
                                 "en": "Error calculating years since start: {exc}"},
    "etf.error_hito":           {"es": "Error al calcular hito para {etf_id}: {exc}",
                                 "en": "Error calculating milestone for {etf_id}: {exc}"},
    "etf.error_download":       {"es": "Error descargando {ticker}: {exc}",
                                 "en": "Error downloading {ticker}: {exc}"},
    "etf.error_volatility":     {"es": "Error calculando volatilidad: {exc}",
                                 "en": "Error calculating volatility: {exc}"},

    # ── ETF monitor — phase labels ──────────────────────────────────────────
    "etf.phase2":               {"es": "FASE 2 — ETFs acelerados",
                                 "en": "PHASE 2 — Accelerated ETFs"},
    "etf.phase1":               {"es": "FASE 1 — Faltan ~{months} meses para Fase 2",
                                 "en": "PHASE 1 — ~{months} months until Phase 2"},

    # ── ETF monitor — signals ───────────────────────────────────────────────
    "signal.mm200.title":       {"es": "⚠️ Precio bajo MM200",
                                 "en": "⚠️ Price below MA200"},
    "signal.mm200.body":        {"es": "Precio ({price:.2f}) bajo MM200 ({mm:.2f}). Tendencia bajista.",
                                 "en": "Price ({price:.2f}) below MA200 ({mm:.2f}). Bearish trend."},
    "signal.mm50.title":        {"es": "📉 Precio bajo MM50",
                                 "en": "📉 Price below MA50"},
    "signal.mm50.body":         {"es": "Precio ({price:.2f}) bajo MM50 ({mm:.2f}). Corrección a corto plazo.",
                                 "en": "Price ({price:.2f}) below MA50 ({mm:.2f}). Short-term correction."},
    "signal.mm_ok.title":       {"es": "✅ Precio sobre ambas medias",
                                 "en": "✅ Price above both MAs"},
    "signal.mm_ok.body":        {"es": "Precio ({price:.2f}) sobre MM50 ({mm50:.2f}) y MM200 ({mm200:.2f}).",
                                 "en": "Price ({price:.2f}) above MA50 ({mm50:.2f}) and MA200 ({mm200:.2f})."},
    "signal.golden.title":      {"es": "🟡 Golden Cross",
                                 "en": "🟡 Golden Cross"},
    "signal.golden.body":       {"es": "MM50 cruzó al alza MM200. Señal de compra técnica.",
                                 "en": "MA50 crossed above MA200. Technical buy signal."},
    "signal.death.title":       {"es": "🔴 Death Cross",
                                 "en": "🔴 Death Cross"},
    "signal.death.body":        {"es": "MM50 cruzó a la baja MM200. Señal bajista fuerte.",
                                 "en": "MA50 crossed below MA200. Strong bearish signal."},
    "signal.drop_severe.title": {"es": "🚨 Caída severa desde máximo",
                                 "en": "🚨 Severe drop from high"},
    "signal.drop_severe.body":  {"es": "{pct:.1%} desde máximo 52s ({high:.2f}). Revisar posición.",
                                 "en": "{pct:.1%} from 52w high ({high:.2f}). Review position."},
    "signal.drop_warn.title":   {"es": "⚠️ Corrección notable",
                                 "en": "⚠️ Notable correction"},
    "signal.drop_warn.body":    {"es": "{pct:.1%} desde máximo 52s ({high:.2f}).",
                                 "en": "{pct:.1%} from 52w high ({high:.2f})."},
    "signal.loss_crit.title":   {"es": "🚨 PÉRDIDA REAL CRÍTICA",
                                 "en": "🚨 CRITICAL REAL LOSS"},
    "signal.loss_crit.body":    {"es": "Perdiendo {pct:.1%} sobre precio medio ({avg:.2f}€).",
                                 "en": "Losing {pct:.1%} vs average cost ({avg:.2f}€)."},
    "signal.loss_warn.title":   {"es": "⚠️ En pérdidas sobre coste",
                                 "en": "⚠️ Below average cost"},
    "signal.loss_warn.body":    {"es": "{pct:.1%} bajo precio medio ({avg:.2f}€).",
                                 "en": "{pct:.1%} below average cost ({avg:.2f}€)."},
    "signal.profit.title":      {"es": "✅ En beneficio",
                                 "en": "✅ In profit"},
    "signal.profit.body":       {"es": "+{pct:.1%} sobre precio medio ({avg:.2f}€).",
                                 "en": "+{pct:.1%} above average cost ({avg:.2f}€)."},
    "signal.volatility.title":  {"es": "📊 Alta volatilidad",
                                 "en": "📊 High volatility"},
    "signal.volatility.body":   {"es": "Volatilidad anualizada: {vol:.1%}.",
                                 "en": "Annualised volatility: {vol:.1%}."},

    # ── ETF monitor — recommendations ──────────────────────────────────────
    "rec.danger.title":         {"es": "🚨 REVISIÓN URGENTE RECOMENDADA",
                                 "en": "🚨 URGENT REVIEW RECOMMENDED"},
    "rec.danger.body":          {"es": "Señales críticas en {name}. Revisa si la tesis sigue vigente. "
                                       "Para ETF de largo plazo, una caída temporal NO justifica vender.",
                                 "en": "Critical signals for {name}. Check if the investment thesis still holds. "
                                       "For long-term ETFs, a temporary drop does NOT justify selling."},
    "rec.warn.title":           {"es": "⚠️ CORRECCIÓN EN CURSO — MANTENER",
                                 "en": "⚠️ CORRECTION UNDERWAY — HOLD"},
    "rec.warn.body":            {"es": "{name} en corrección. Mantén y sigue aportando: "
                                       "cada euro en corrección baja tu precio medio.",
                                 "en": "{name} in correction. Hold and keep contributing: "
                                       "every euro invested in a correction lowers your average cost."},
    "rec.ok.title":             {"es": "✅ TODO EN ORDEN — CONTINUAR PLAN",
                                 "en": "✅ ALL GOOD — CONTINUE PLAN"},
    "rec.ok.body":              {"es": "{name} sigue tendencia positiva. Mantén los savings plans activos.",
                                 "en": "{name} following positive trend. Keep savings plans active."},

    # ── ETF monitor — email ─────────────────────────────────────────────────
    "email.subject_etf":        {"es": "Estado ETFs",
                                 "en": "ETF Status"},
    "email.no_pass":            {"es": "Email no enviado: GMAIL_PASS no configurado.",
                                 "en": "Email not sent: GMAIL_PASS not configured."},
    "email.no_creds":           {"es": "Credenciales email incompletas — email deshabilitado",
                                 "en": "Incomplete email credentials — email disabled"},
    "email.sent":               {"es": "📧 Email enviado correctamente.",
                                 "en": "📧 Email sent successfully."},
    "email.error_auth":         {"es": "Error de autenticación SMTP: {exc}",
                                 "en": "SMTP authentication error: {exc}"},
    "email.error_smtp":         {"es": "Error SMTP: {exc}",
                                 "en": "SMTP error: {exc}"},
    "email.error_conn":         {"es": "Error de conexión: {exc}",
                                 "en": "Connection error: {exc}"},
    "email.error_unexpected":   {"es": "Error inesperado enviando email: {exc}",
                                 "en": "Unexpected error sending email: {exc}"},

    # ── Crypto monitor — __main__ ───────────────────────────────────────────
    "crypto.fetching_prices":   {"es": "📡 Obteniendo precios...",
                                 "en": "📡 Fetching prices..."},
    "crypto.fetching_market":   {"es": "📊 Obteniendo datos de mercado y OHLC...",
                                 "en": "📊 Fetching market data and OHLC..."},
    "crypto.fetching_fg":       {"es": "📈 Obteniendo Fear & Greed...",
                                 "en": "📈 Fetching Fear & Greed..."},
    "crypto.generating_html":   {"es": "🖊️ Generando HTML...",
                                 "en": "🖊️ Generating HTML..."},
    "crypto.report_generated":  {"es": "✅ Reporte generado: {path}",
                                 "en": "✅ Report generated: {path}"},

    # ── Crypto monitor — api ────────────────────────────────────────────────
    "crypto.error_prices":      {"es": "Error obteniendo precios: {exc}",
                                 "en": "Error fetching prices: {exc}"},
    "crypto.error_ohlc":        {"es": "Error obteniendo OHLC para {cg_id}: {exc}",
                                 "en": "Error fetching OHLC for {cg_id}: {exc}"},
    "crypto.error_market":      {"es": "Error obteniendo market data para {cg_id}: {exc}",
                                 "en": "Error fetching market data for {cg_id}: {exc}"},
    "crypto.error_fg":          {"es": "Error obteniendo Fear & Greed: {exc}",
                                 "en": "Error fetching Fear & Greed: {exc}"},

    # ── Crypto monitor — signals ────────────────────────────────────────────
    "crypto.fg_extreme_greed":  {"es": "🔴 Fear & Greed en Codicia Extrema ({val}). Considera reducir exposición.",
                                 "en": "🔴 Fear & Greed at Extreme Greed ({val}). Consider reducing exposure."},
    "crypto.fg_high_greed":     {"es": "🟡 Fear & Greed elevado ({val}). Vigilar posible corrección.",
                                 "en": "🟡 Fear & Greed high ({val}). Watch for possible correction."},
    "crypto.fg_extreme_fear":   {"es": "🟢 Fear & Greed en Miedo Extremo ({val}). Buen momento de mantener/acumular.",
                                 "en": "🟢 Fear & Greed at Extreme Fear ({val}). Good time to hold/accumulate."},
    "crypto.drop_danger":       {"es": "🔴 Caída de {pct:.1f}% en 24h. Vigilar si continúa.",
                                 "en": "🔴 Drop of {pct:.1f}% in 24h. Watch if it continues."},
    "crypto.drop_warn":         {"es": "🟡 Caída de {pct:.1f}% en 24h.",
                                 "en": "🟡 Drop of {pct:.1f}% in 24h."},
    "crypto.pump_warn":         {"es": "🟡 Subida fuerte +{pct:.1f}% en 24h. Posible corrección próxima.",
                                 "en": "🟡 Strong surge +{pct:.1f}% in 24h. Possible correction ahead."},
    "crypto.ath_danger":        {"es": "🔴 A solo {pct:.1f}% del ATH. Considera vender un porcentaje.",
                                 "en": "🔴 Only {pct:.1f}% from ATH. Consider selling a portion."},
    "crypto.ath_warn":          {"es": "🟡 A {pct:.1f}% del ATH. Empieza a planificar salida parcial.",
                                 "en": "🟡 {pct:.1f}% from ATH. Start planning a partial exit."},
    "crypto.bear_30d":          {"es": "🟡 Bajada del {pct:.1f}% en 30 días. Tendencia bajista sostenida.",
                                 "en": "🟡 Down {pct:.1f}% in 30 days. Sustained bearish trend."},
    "crypto.bull_30d":          {"es": "🟢 Subida del +{pct:.1f}% en 30 días. Tendencia alcista fuerte.",
                                 "en": "🟢 Up +{pct:.1f}% in 30 days. Strong bullish trend."},

    # ── Crypto monitor — report labels ─────────────────────────────────────
    "crypto.status_danger":     {"es": "⚠️ ACCIÓN RECOMENDADA — Revisa las alertas rojas",
                                 "en": "⚠️ ACTION REQUIRED — Review red alerts"},
    "crypto.status_warning":    {"es": "🔔 HAY AVISOS — Revisa las alertas amarillas",
                                 "en": "🔔 WARNINGS — Review yellow alerts"},
    "crypto.status_ok":         {"es": "✅ TODO TRANQUILO — No hay acciones urgentes hoy",
                                 "en": "✅ ALL CLEAR — No urgent actions today"},
    "crypto.no_alerts":         {"es": "✅ Sin alertas para este activo",
                                 "en": "✅ No alerts for this asset"},
    "crypto.available_now":     {"es": "Disponible ahora",
                                 "en": "Available now"},
    "crypto.available_rescue":  {"es": "Disponible en {days}d (rescate)",
                                 "en": "Available in {days}d (redemption)"},
    "crypto.available_in":      {"es": "Disponible en {days}d",
                                 "en": "Available in {days}d"},
    "crypto.matures":           {"es": "Vence: {date}",
                                 "en": "Matures: {date}"},
    "crypto.next_reward":       {"es": "Próxima recompensa: {days}d",
                                 "en": "Next reward: {days}d"},
    "crypto.flexible":          {"es": "Flexible",
                                 "en": "Flexible"},
    "crypto.label_amount":      {"es": "Cantidad:",
                                 "en": "Amount:"},
    "crypto.label_value":       {"es": "Valor actual:",
                                 "en": "Current value:"},
    "crypto.label_product":     {"es": "Producto:",
                                 "en": "Product:"},
    "crypto.label_daily_gain":  {"es": "Ganancia/día:",
                                 "en": "Daily gain:"},
    "crypto.label_accumulated": {"es": "Acumulado staking:",
                                 "en": "Staking accumulated:"},
    "crypto.report_title":      {"es": "Informe de Criptomonedas",
                                 "en": "Cryptocurrency Report"},
    "crypto.report_subtitle":   {"es": "Generado el {date} · Ordenado por proximidad de acción",
                                 "en": "Generated on {date} · Sorted by action proximity"},
    "crypto.footer_note":       {"es": "Datos vía CoinGecko · Fear & Greed vía alternative.me",
                                 "en": "Data via CoinGecko · Fear & Greed via alternative.me"},

    # ── Crypto monitor — email ──────────────────────────────────────────────
    "email.subject_crypto":     {"es": "📊 Informe Cripto — {date}",
                                 "en": "📊 Crypto Report — {date}"},
    "email.no_creds_crypto":    {"es": "GMAIL_USER / GMAIL_PASS no definidos — saltando envío.",
                                 "en": "GMAIL_USER / GMAIL_PASS not set — skipping email."},

    # Alert level labels (user-facing, go through i18n)
    "alert.ok":     {"es": "EN ORDEN",    "en": "ON TRACK"},
    "alert.info":   {"es": "INFORMATIVO", "en": "INFO"},
    "alert.warn":   {"es": "CORRECCIÓN",  "en": "CORRECTION"},
    "alert.danger": {"es": "REVISAR",     "en": "REVIEW"},

    # Shared delivery
    "delivery.saved":            {"es": "✅ Informe guardado: {path}",
                                  "en": "✅ Report saved: {path}"},
    "delivery.save_error":       {"es": "Error guardando informe: {exc}",
                                  "en": "Error saving report: {exc}"},
    "delivery.no_creds_fallback":{"es": "Sin credenciales email — guardando informe en disco.",
                                  "en": "No email credentials — saving report to disk."},

    # ETF report — UI labels
    "etf.ui.total_title":        {"es": "💰 Dinero Total en ETFs",
                                  "en": "💰 Total ETF Portfolio"},
    "etf.ui.updated":            {"es": "Actualizado: {ts}",
                                  "en": "Updated: {ts}"},
    "etf.ui.today":              {"es": "{pct} hoy",
                                  "en": "{pct} today"},
    "etf.ui.portfolio_value":    {"es": "Valor cartera",
                                  "en": "Portfolio value"},
    "etf.ui.gain_loss":          {"es": "Ganancia/pérdida",
                                  "en": "Gain/loss"},
    "etf.ui.status_header":      {"es": "📊 Estado actual de la cartera",
                                  "en": "📊 Current portfolio status"},
    "etf.ui.detail_header":      {"es": "🔍 Análisis detallado",
                                  "en": "🔍 Detailed analysis"},
    "etf.ui.plan_header":        {"es": "🗺️ Plan de inversión — Estado actual",
                                  "en": "🗺️ Investment plan — Current status"},
    "etf.ui.technical":          {"es": "Análisis técnico",
                                  "en": "Technical analysis"},
    "etf.ui.position":           {"es": "Tu posición",
                                  "en": "Your position"},
    "etf.ui.high_52w":           {"es": "Máx 52 semanas",
                                  "en": "52w high"},
    "etf.ui.low_52w":            {"es": "Mín 52 semanas",
                                  "en": "52w low"},
    "etf.ui.ma50":               {"es": "Media móvil 50d",
                                  "en": "50d moving avg"},
    "etf.ui.ma200":              {"es": "Media móvil 200d",
                                  "en": "200d moving avg"},
    "etf.ui.annual_vol":         {"es": "Volatilidad anual",
                                  "en": "Annual volatility"},
    "etf.ui.drawdown":           {"es": "Caída vs máx 52s",
                                  "en": "Drop vs 52w high"},
    "etf.ui.units":              {"es": "Participaciones",
                                  "en": "Units held"},
    "etf.ui.avg_cost":           {"es": "Precio medio compra",
                                  "en": "Average cost"},
    "etf.ui.current_value":      {"es": "Valor actual",
                                  "en": "Current value"},
    "etf.ui.gain_eur":           {"es": "Ganancia/pérdida €",
                                  "en": "Gain/loss €"},
    "etf.ui.gain_pct":           {"es": "Ganancia/pérdida %",
                                  "en": "Gain/loss %"},
    "etf.ui.monthly_contrib":    {"es": "Aportación mensual",
                                  "en": "Monthly contribution"},
    "etf.ui.contrib_amount":     {"es": "{amount:.0f} €/mes",
                                  "en": "{amount:.0f} €/mo"},
    "etf.ui.signals_header":     {"es": "Señales detectadas",
                                  "en": "Detected signals"},
    "etf.ui.chg_1d":             {"es": "1 día",   "en": "1 day"},
    "etf.ui.chg_1m":             {"es": "1 mes",   "en": "1 month"},
    "etf.ui.chg_3m":             {"es": "3 meses", "en": "3 months"},
    "etf.ui.chg_ytd":            {"es": "Año actual", "en": "YTD"},
    "etf.ui.tax_title":          {"es": "💶 Si vendieras hoy — Impacto fiscal",
                                  "en": "💶 If you sold today — Tax impact"},
    "etf.ui.tax_gross":          {"es": "Ganancia/pérdida bruta",
                                  "en": "Gross gain/loss"},
    "etf.ui.tax_irpf":           {"es": "Impuesto a pagar (IRPF)",
                                  "en": "Tax due (IRPF)"},
    "etf.ui.tax_net":            {"es": "Dinero real a bolsillo",
                                  "en": "Net cash in hand"},
    "etf.ui.tax_set_aside":      {"es": "⚠️ <strong>Guarda {amount:,.0f} € aparte</strong> si vendes.",
                                  "en": "⚠️ <strong>Set aside {amount:,.0f} €</strong> if you sell."},
    "etf.ui.proj_title":         {"es": "📊 Seguimiento del plan — Año {year}",
                                  "en": "📊 Plan tracking — Year {year}"},
    "etf.ui.proj_expected":      {"es": "Valor proyectado (año {year})",
                                  "en": "Projected value (year {year})"},
    "etf.ui.proj_actual":        {"es": "Valor real actual",
                                  "en": "Current actual value"},
    "etf.ui.proj_deviation":     {"es": "Desviación vs plan",
                                  "en": "Deviation vs plan"},
    "etf.ui.phase2_active":      {"es": "✅ FASE 2 — ETFs acelerados",
                                  "en": "✅ PHASE 2 — Accelerated ETFs"},
    "etf.ui.phase2_body":        {"es": "TR lleno · Todo el ahorro mensual va a ETFs.",
                                  "en": "TR full · All monthly savings go to ETFs."},
    "etf.ui.phase1_active":      {"es": "⏳ FASE 1 — Rellenando Trade Republic",
                                  "en": "⏳ PHASE 1 — Filling Trade Republic"},
    "etf.ui.phase1_body":        {"es": "Faltan <strong>{months} meses</strong> para Fase 2 ({date}).",
                                  "en": "<strong>{months} months</strong> left until Phase 2 ({date})."},
    "etf.ui.milestone_header":   {"es": "Hito proyectado — Año {year}",
                                  "en": "Projected milestone — Year {year}"},
    "etf.ui.milestone_expected": {"es": "Valor total ETFs esperado",
                                  "en": "Expected total ETF value"},
    "etf.ui.milestone_actual":   {"es": "Valor total ETFs actual",
                                  "en": "Current total ETF value"},
    "etf.ui.milestone_gain":     {"es": "Ganancia/pérdida total",
                                  "en": "Total gain/loss"},
    "etf.ui.contrib_header":     {"es": "Aportaciones actuales",
                                  "en": "Current contributions"},
    "etf.ui.disclaimer_title":   {"es": "⚠️ Aviso importante",
                                  "en": "⚠️ Important notice"},
    "etf.ui.disclaimer_body":    {"es": "Este monitor usa señales técnicas como indicadores de alerta, no como predicciones. "
                                        "Para ETF de largo plazo, la acción correcta en corrección es mantener y seguir aportando.",
                                  "en": "This monitor uses technical signals as alert indicators, not predictions. "
                                        "For long-term ETFs, the right action during a correction is to hold and keep contributing."},
    "etf.ui.report_title":       {"es": "📈 Monitor de Cartera ETF",
                                  "en": "📈 ETF Portfolio Monitor"},

    # Crypto report — UI labels
    "crypto.ui.sparkline_period":{"es": "30 días", "en": "30 days"},
    "crypto.ui.kucoin_btn":      {"es": "🚀 Abrir KuCoin Earn",
                                  "en": "🚀 Open KuCoin Earn"},
}

# ---------------------------------------------------------------------------
# Language resolution
# ---------------------------------------------------------------------------
_SUPPORTED = {"es", "en"}
_DEFAULT   = "es"


def _resolve_lang() -> str:
    """Resolve active language: env var > default."""
    lang = os.environ.get("MONITOR_LANG", _DEFAULT).lower()
    return lang if lang in _SUPPORTED else _DEFAULT


def t(key: str, **kwargs: Any) -> str:
    """
    Return the translated string for *key* in the active language.
    Keyword arguments are interpolated via str.format_map.
    Falls back to the key itself if not found.
    """
    lang   = _resolve_lang()
    entry  = _CATALOGUE.get(key, {})
    text   = entry.get(lang) or entry.get(_DEFAULT) or key
    return text.format_map(kwargs) if kwargs else text
