"""
Unit conversion utilities.

All conversions use standard factors and are pure functions.
"""


def kmh_to_mph(kmh: float) -> float:
    """Convert kilometres per hour to miles per hour."""
    return kmh * 0.621371


def mm_to_inches(mm: float) -> float:
    """Convert millimetres to inches."""
    return mm / 25.4


def cm_to_inches(cm: float) -> float:
    """Convert centimetres to inches."""
    return cm / 2.54


def meters_to_miles(m: float) -> float:
    """Convert metres to miles."""
    return m / 1609.344


def miles_to_meters(miles: float) -> float:
    """Convert miles to metres."""
    return miles * 1609.344
