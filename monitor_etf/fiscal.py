"""
monitor_etf/fiscal.py — Spanish IRPF capital gains tax calculation.
"""
from typing import Dict, Optional

from .thresholds import PLAN


def calculate_tax(gain: float) -> float:
    """Calculate IRPF tax on a capital gain using progressive brackets."""
    if gain <= 0:
        return 0.0
    total     = 0.0
    remaining = gain
    for limit, rate in PLAN["tax_brackets"]:
        amount     = min(remaining, limit)
        total     += amount * rate
        remaining -= amount
        if remaining <= 0:
            break
    return total


def calculate_tax_impact(
    units: float,
    avg_cost: Optional[float],
    current_price: float,
) -> Optional[Dict[str, float]]:
    """Calculate tax impact if the position were sold today."""
    if not avg_cost or units <= 0:
        return None
    current_value = units * current_price
    cost_basis    = units * avg_cost
    gain          = current_value - cost_basis
    if gain <= 0:
        return {"gain": gain, "tax": 0.0, "net": current_value, "set_aside": 0.0}
    tax = calculate_tax(gain)
    return {
        "gain":      gain,
        "tax":       tax,
        "net":       current_value - tax,
        "set_aside": tax,
    }
