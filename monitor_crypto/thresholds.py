"""
monitor_crypto/thresholds.py — Re-exports crypto configuration from shared/config_loader.py.

To change any value, edit settings.toml in the project root.
"""
from shared.config_loader import (  # noqa: F401
    ATH_DANGER_PCT,
    ATH_WARN_PCT,
    CHANGE_24H_DANGER,
    CHANGE_24H_PUMP,
    CHANGE_24H_WARN,
    CHANGE_30D_BEAR,
    CHANGE_30D_BULL,
    EMAIL_CONFIG,
    FG_EXTREME_FEAR,
    FG_EXTREME_GREED,
    FG_HIGH_GREED,
    POSITIONS,
)
