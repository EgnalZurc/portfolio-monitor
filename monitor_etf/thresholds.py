"""
monitor_etf/thresholds.py — Re-exports ETF configuration from shared/config_loader.py.

To change any value, edit settings.toml in the project root.
"""
from shared.config_loader import (  # noqa: F401
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
