# Egnal Portfolio Monitor

Daily automated monitors for **ETF portfolios** and **cryptocurrency staking positions**. They run automatically every weekday via GitHub Actions and send an HTML report by email.

**Crypto monitor focus:** This monitor is specifically designed for tracking staking positions (flexible and fixed-term products). It shows days until redemption, daily/accumulated staking rewards, and market signals relevant to staking renewal decisions.

---

## Project structure

```
control/
├── settings.toml          ← THE only file you need to edit
├── monitor_etf/
│   ├── __main__.py        Entry point
│   ├── analysis.py        Data download and technical analysis
│   ├── config.py          Re-exports from shared/settings.py
│   ├── email_sender.py    Email delivery
│   ├── fiscal.py          IRPF tax calculation
│   ├── models.py          AlertLevel enum
│   └── report.py          HTML report generation
├── monitor_crypto/
│   ├── __main__.py        Entry point
│   ├── api.py             CoinGecko + Fear & Greed API calls
│   ├── config.py          Re-exports from shared/settings.py
│   ├── email_sender.py    Email delivery
│   ├── report.py          HTML report generation
│   └── signals.py        Signal logic
├── shared/
│   ├── i18n.py            Translations (es / en)
│   ├── settings.py        Loads settings.toml and exposes typed config
│   └── utils.py           Shared timezone utilities
└── requirements.txt
```

---

## Running locally

```bash
pip install -r requirements.txt

python -m monitor_etf              # ETF monitor (opens browser)
python -m monitor_crypto           # Crypto monitor (opens browser)

python -m monitor_etf --no-browser    # No browser (same as CI)
python -m monitor_crypto --no-browser
```

---

## Required environment variables

| Variable      | Description                                          |
|---------------|------------------------------------------------------|
| `GMAIL_USER`  | Gmail account used to send reports                   |
| `GMAIL_PASS`  | Gmail App Password (not your regular password)       |
| `TO_EMAIL`    | Recipient address (optional — defaults to GMAIL_USER)|
| `MONITOR_LANG`| Report language: `es` or `en` (optional — defaults to `settings.toml`) |

Credentials are **never** stored in `settings.toml`. Set them as GitHub Secrets or local environment variables.

---

## Configuration reference — settings.toml

All configuration lives in `settings.toml` at the project root.
**You never need to edit any Python file.**

---

### [general]

```toml
[general]
lang = "es"
```

| Key    | Type   | Description                                                  |
|--------|--------|--------------------------------------------------------------|
| `lang` | string | Default report language. `"es"` = Spanish, `"en"` = English. Can be overridden at runtime with the `MONITOR_LANG` environment variable. |

---

### [[etf.funds]]

One block per ETF. Add as many blocks as you need.

```toml
[[etf.funds]]
id               = "FUND1"
ticker           = "FUND1.L"
name             = "Example ETF Fund"
isin             = "IE00XXXXXXXX"
precio_medio     = 0.0
participaciones  = 0.0
aportacion_mes   = 100.0
aportacion_fase2 = 500.0
inicio           = "2024-01-01"
color            = "#3A7BD5"
```

| Key                | Type   | Description |
|--------------------|--------|-------------|
| `id`               | string | Unique identifier used in logs and reports. Must be unique across all funds. |
| `ticker`           | string | Yahoo Finance ticker symbol (e.g. `"IUIT.L"`, `"VWCE.DE"`). |
| `name`             | string | Full fund name shown in the HTML report. |
| `isin`             | string | ISIN identifier shown in the report. |
| `precio_medio`     | float  | Weighted average purchase price in EUR. Use `0.0` if no units held yet. Recalculate after each purchase: `(prev_avg × prev_units + buy_price × new_units) / total_units`. |
| `participaciones`  | float  | Total units currently held (from your broker statement). Use `0.0` if none yet. |
| `aportacion_mes`   | float  | Monthly contribution in EUR during Phase 1 (before `phase_change_date`). |
| `aportacion_fase2` | float  | Monthly contribution in EUR once Phase 2 is active. |
| `inicio`           | string | Date of first purchase in `YYYY-MM-DD` format. Used to calculate years invested. Leave empty `""` to default to today. |
| `color`            | string | Hex accent colour used in the HTML report (e.g. `"#3A7BD5"`). |

---

### [etf.plan]

```toml
[etf.plan]
phase_change_date = "2027-03-01"

[etf.plan.milestones]
1  = [1_800,  1_257]
2  = [3_352,  3_643]
10 = [147_918, 168_587]
```

| Key                  | Type   | Description |
|----------------------|--------|-------------|
| `phase_change_date`  | string | Estimated date (`YYYY-MM-DD`) when Phase 2 begins (e.g. when Trade Republic reaches 100,000 €). After this date, `aportacion_fase2` is used instead of `aportacion_mes`. |
| `milestones`         | table  | Projected total portfolio value per year of investment. Each key is the year number (integer). Each value is an array of EUR amounts, one per fund, **in the same order as the `[[etf.funds]]` blocks**. Used to track progress against the original plan. |

**Milestone example with 3 funds:**
```toml
[etf.plan.milestones]
# year = [FUND1_eur, FUND2_eur, FUND3_eur]
1  = [1_000,  1_000,   500]
2  = [3_000,  3_000, 1_200]
```

---

### [etf.tax]

```toml
[etf.tax]
brackets = [
    [6_000,        0.19],
    [44_000,       0.21],
    [150_000,      0.23],
    [999_999_999,  0.27],
]
```

| Key        | Type  | Description |
|------------|-------|-------------|
| `brackets` | array | Spanish IRPF capital gains tax brackets for 2026. Each entry is `[upper_limit_eur, rate]`. The last bracket must use `999_999_999` to represent no upper limit. Update rates each year if the tax law changes. |

---

### [etf.thresholds]

```toml
[etf.thresholds]
ma_short            = 50
ma_long             = 200
drop_from_high_warn = -0.15
loss_vs_cost_warn   = -0.10
critical_threshold  = -0.20
```

| Key                  | Type  | Description |
|----------------------|-------|-------------|
| `ma_short`           | int   | Short moving average window in trading days (default: 50). |
| `ma_long`            | int   | Long moving average window in trading days (default: 200). |
| `drop_from_high_warn`| float | Warn when price drops this fraction from its 52-week high. `-0.15` = warn at -15%. |
| `loss_vs_cost_warn`  | float | Warn when position is this fraction below average purchase price. `-0.10` = warn at -10%. |
| `critical_threshold` | float | Critical alert level for both drop-from-high and loss-vs-cost. `-0.20` = alert at -20%. |

---

### [[crypto.positions]]

One block per **staking position**. The crypto monitor is focused exclusively on staking — it tracks days until redemption, accumulated rewards, and market signals relevant to renewal decisions. Add as many blocks as you need.

```toml
[[crypto.positions]]
symbol                 = "ETH"
name                   = "Ethereum"
amount                 = 0.0
product                = "Flexible Stake"
apy                    = 2.14
type                   = "flexible"
rescue_days            = 5
start_date             = "2026-04-20"
next_distribution      = "2026-04-22"
distribution_freq_days = 2
coingecko_id           = "ethereum"
```

| Key                     | Type   | Description |
|-------------------------|--------|-------------|
| `symbol`                | string | Asset ticker (e.g. `"ETH"`, `"BTC"`, `"SOL"`). Shown in the report. |
| `name`                  | string | Full asset name (e.g. `"Ethereum"`). |
| `amount`                | float  | Units currently staked. Update after each change in KuCoin Earn. |
| `product`               | string | KuCoin product name shown in the report (e.g. `"Flexible Stake"`, `"Fijo 60 días"`). |
| `apy`                   | float  | Annual percentage yield as a percentage (e.g. `2.14` = 2.14% APY). |
| `type`                  | string | `"flexible"` = redeemable with notice. `"fixed"` = locked until `maturity_date`. |
| `rescue_days`           | int    | Business days required to redeem a flexible position. Use `0` for fixed. |
| `start_date`            | string | Date staking started (`YYYY-MM-DD`). Used to calculate accumulated earnings. |
| `next_distribution`     | string | Next reward distribution date (`YYYY-MM-DD`). **Update after each distribution.** Only for flexible positions. |
| `distribution_freq_days`| int    | How often rewards are distributed in days (e.g. `2` = every 2 days). Only for flexible positions. |
| `maturity_date`         | string | Date the fixed-term product matures (`YYYY-MM-DD`). Only for `type = "fixed"`. |
| `coingecko_id`          | string | CoinGecko asset ID used to fetch price and market data. Find it at [coingecko.com](https://www.coingecko.com) in the asset URL (e.g. `"ethereum"`, `"solana"`, `"bitcoin"`). |

---

### [crypto.thresholds]

```toml
[crypto.thresholds]
fg_extreme_greed  = 80
fg_high_greed     = 65
fg_extreme_fear   = 20
change_24h_danger = -10
change_24h_warn   = -5
change_24h_pump   = 10
change_30d_bear   = -20
change_30d_bull   =  20
ath_danger_pct    = -5
ath_warn_pct      = -15
```

| Key                | Type  | Description |
|--------------------|-------|-------------|
| `fg_extreme_greed` | int   | Fear & Greed index: danger alert above this value (default: 80). |
| `fg_high_greed`    | int   | Fear & Greed index: warning above this value (default: 65). |
| `fg_extreme_fear`  | int   | Fear & Greed index: accumulation opportunity below this value (default: 20). |
| `change_24h_danger`| float | 24h price change: danger alert below this percentage (default: -10%). |
| `change_24h_warn`  | float | 24h price change: warning below this percentage (default: -5%). |
| `change_24h_pump`  | float | 24h price change: warning above this percentage — possible correction (default: +10%). |
| `change_30d_bear`  | float | 30-day change: bearish trend warning below this percentage (default: -20%). |
| `change_30d_bull`  | float | 30-day change: bullish trend signal above this percentage (default: +20%). |
| `ath_danger_pct`   | float | Distance from ATH: danger alert when closer than this (default: -5%). |
| `ath_warn_pct`     | float | Distance from ATH: warning when closer than this (default: -15%). |

---

## How to add a new ETF

**1. Find the Yahoo Finance ticker**

Go to [finance.yahoo.com](https://finance.yahoo.com) and search for the fund.
Copy the ticker symbol shown in the URL or next to the fund name (e.g. `VWCE.DE`).

**2. Add a block to settings.toml**

```toml
[[etf.funds]]
id               = "VWCE"
ticker           = "VWCE.DE"
name             = "Vanguard FTSE All-World UCITS ETF Acc"
isin             = "IE00BK5BQT80"
precio_medio     = 0.0        # set after first purchase
participaciones  = 0.0        # set after first purchase
aportacion_mes   = 200.0
aportacion_fase2 = 200.0
inicio           = ""         # will default to today
color            = "#E67E22"  # pick any hex colour
```

**3. Add a milestone column (optional)**

If you track projections, add a third value to each milestone row.
The order must match the order of `[[etf.funds]]` blocks:

```toml
[etf.plan.milestones]
# year = [IUIT_eur, IWDA_eur, VWCE_eur]
1  = [1_800,    1_257,   200]
2  = [3_352,    3_643,   500]
```

**4. That's it.** No Python files need to be changed.

---

## How to add a new crypto staking position

**1. Find the CoinGecko ID**

Go to [coingecko.com](https://www.coingecko.com), search for the asset,
and copy the last segment of the URL:
`https://www.coingecko.com/en/coins/ethereum` → ID is `ethereum`.

**Note:** This monitor tracks staking positions only. It is not a general trading monitor.

**2. Add a block to settings.toml**

For a **flexible** position:

```toml
[[crypto.positions]]
symbol                 = "ADA"
name                   = "Cardano"
amount                 = 500.0
product                = "Flexible Stake"
apy                    = 3.50
type                   = "flexible"
rescue_days            = 3
start_date             = "2026-05-01"
next_distribution      = "2026-05-03"
distribution_freq_days = 2
coingecko_id           = "cardano"
```

For a **fixed-term** position:

```toml
[[crypto.positions]]
symbol        = "DOT"
name          = "Polkadot"
amount        = 10.0
product       = "Fixed 30 days"
apy           = 8.00
type          = "fixed"
rescue_days   = 0
start_date    = "2026-05-01"
maturity_date = "2026-05-31"
coingecko_id  = "polkadot"
```

**3. That's it.** No Python files need to be changed.

---

## After a monthly ETF purchase

Update these two fields in the relevant `[[etf.funds]]` block:

```toml
precio_medio    = 33.10   # new weighted average
participaciones = 27.4500 # new total units
```

**Weighted average formula:**
```
new_avg = (prev_avg × prev_units + purchase_price × new_units) / (prev_units + new_units)
```

---

## After a staking change

| Event                        | Field to update              |
|------------------------------|------------------------------|
| Reward received              | `next_distribution`          |
| Staked more units            | `amount`                     |
| Redeemed units               | `amount`                     |
| Renewed a fixed-term product | `start_date`, `maturity_date`|
| APY changed                  | `apy`                        |
