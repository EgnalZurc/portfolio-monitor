"""
monitor_crypto/config.py — Re-exports crypto configuration from shared/settings.py.

To change any value, edit settings.toml in the project root.
"""
from shared.settings import (  # noqa: F401  (re-exported for backward compatibility)
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
