"""
monitor_etf/config.py — Re-exports ETF configuration from shared/settings.py.

To change any value, edit settings.toml in the project root.
"""
from shared.settings import (  # noqa: F401
    ALERTA_CAIDA_DESDE_MAX,
    ALERTA_PERDIDA_REAL,
    ALERTA_VENTA_CRITICA,
    CARTERA,
    EMAIL_CONFIG,
    MM_CORTA,
    MM_LARGA,
    PLAN,
)
