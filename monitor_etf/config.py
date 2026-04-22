"""
monitor_etf/config.py — Re-exports ETF configuration from shared/settings.py.

To change any value, edit settings.toml in the project root.
"""
from shared.settings import (  # noqa: F401
    CRITICAL_THRESHOLD,
    DROP_FROM_HIGH_WARN,
    EMAIL_CONFIG,
    FUND_IDS,
    LOSS_VS_COST_WARN,
    MA_LONG,
    MA_SHORT,
    PLAN,
    PORTFOLIO,
)
