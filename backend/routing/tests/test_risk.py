import math
import pytest

from routing.domain.models import RiskLevel, WeatherData
from routing.domain.risk import (
    apply_load_rules,
    assess_checkpoint_risk,
    classify_rain,
    classify_snow,
    classify_wind,
)


@pytest.mark.parametrize(
    ("wind_mph", "expected_risk"),
    [
        (0.0, RiskLevel.LOW),
        (24.9, RiskLevel.LOW),
        (25.0, RiskLevel.MODERATE),
        (34.9, RiskLevel.MODERATE),
        (35.0, RiskLevel.HIGH),
        (44.9, RiskLevel.HIGH),
        (45.0, RiskLevel.SEVERE),
        (54.9, RiskLevel.SEVERE),
        (55.0, RiskLevel.NO_TRAVEL),
        (65.0, RiskLevel.NO_TRAVEL),
    ],
)
def test_wind_boundaries(wind_mph: float, expected_risk: RiskLevel) -> None:
    assert classify_wind(wind_mph) == expected_risk


def test_wind_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="NaN"):
        classify_wind(float("nan"))
    assert classify_wind(-5.0) == RiskLevel.LOW


@pytest.mark.parametrize(
    ("rain_in_per_hour", "expected_risk"),
    [
        (0.0, RiskLevel.LOW),
        (0.099, RiskLevel.LOW),
        (0.10, RiskLevel.MODERATE),
        (0.249, RiskLevel.MODERATE),
        (0.25, RiskLevel.HIGH),
        (0.499, RiskLevel.HIGH),
        (0.50, RiskLevel.SEVERE),
        (1.00, RiskLevel.SEVERE),
        (1.001, RiskLevel.NO_TRAVEL),
        (2.5, RiskLevel.NO_TRAVEL),
    ],
)
def test_rain_boundaries(rain_in_per_hour: float, expected_risk: RiskLevel) -> None:
    assert classify_rain(rain_in_per_hour) == expected_risk


def test_rain_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="NaN"):
        classify_rain(float("nan"))
    assert classify_rain(-0.1) == RiskLevel.LOW


@pytest.mark.parametrize(
    ("snow_in_per_hour", "expected_risk"),
    [
        (0.0, RiskLevel.LOW),
        (0.49, RiskLevel.LOW),
        (0.50, RiskLevel.MODERATE),
        (0.99, RiskLevel.MODERATE),
        (1.0, RiskLevel.HIGH),
        (1.99, RiskLevel.HIGH),
        (2.0, RiskLevel.SEVERE),
        (3.0, RiskLevel.SEVERE),
        (3.01, RiskLevel.NO_TRAVEL),
        (4.5, RiskLevel.NO_TRAVEL),
    ],
)
def test_snow_boundaries(snow_in_per_hour: float, expected_risk: RiskLevel) -> None:
    assert classify_snow(snow_in_per_hour) == expected_risk


def test_snow_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="NaN"):
        classify_snow(float("nan"))
    assert classify_snow(-1.0) == RiskLevel.LOW


@pytest.mark.parametrize(
    ("wind_mph", "load_weight_lb", "expected_risk", "has_adjustments"),
    [
        (55.0, 10_000.0, RiskLevel.NO_TRAVEL, False),
        (55.0, 50_000.0, RiskLevel.NO_TRAVEL, False),
        (50.0, 30_000.0, RiskLevel.SEVERE, False),
        (50.0, 30_001.0, RiskLevel.NO_TRAVEL, True),
        (45.0, 30_000.0, RiskLevel.SEVERE, False),
        (45.0, 30_001.0, RiskLevel.NO_TRAVEL, True),
        (45.0, 40_000.0, RiskLevel.NO_TRAVEL, True),
        (40.0, 40_000.0, RiskLevel.HIGH, False),
        (40.0, 40_001.0, RiskLevel.SEVERE, True),
        (35.0, 40_001.0, RiskLevel.SEVERE, True),
        (34.9, 50_000.0, RiskLevel.MODERATE, False),
        (20.0, 60_000.0, RiskLevel.LOW, False),
    ],
)
def test_load_rules(
    wind_mph: float,
    load_weight_lb: float,
    expected_risk: RiskLevel,
    has_adjustments: bool,
) -> None:
    base_risk = classify_wind(wind_mph)
    adjusted_risk, adjustments = apply_load_rules(base_risk, wind_mph, load_weight_lb)
    assert adjusted_risk == expected_risk
    assert bool(adjustments) == has_adjustments


def test_no_travel_overrides_all() -> None:
    w1 = WeatherData(
        forecast_at="2026-11-10T12:00:00Z",
        wind_mph=56.0,
        rain_in_per_hour=0.0,
        snow_in_per_hour=0.0,
        source="test",
        available=True,
    )
    risk1 = assess_checkpoint_risk(w1, load_weight_lb=20_000)
    assert risk1.overall == RiskLevel.NO_TRAVEL

    w2 = WeatherData(
        forecast_at="2026-11-10T12:00:00Z",
        wind_mph=10.0,
        rain_in_per_hour=1.2,
        snow_in_per_hour=0.0,
        source="test",
        available=True,
    )
    risk2 = assess_checkpoint_risk(w2, load_weight_lb=20_000)
    assert risk2.overall == RiskLevel.NO_TRAVEL

    w3 = WeatherData(
        forecast_at="2026-11-10T12:00:00Z",
        wind_mph=15.0,
        rain_in_per_hour=0.0,
        snow_in_per_hour=3.5,
        source="test",
        available=True,
    )
    risk3 = assess_checkpoint_risk(w3, load_weight_lb=20_000)
    assert risk3.overall == RiskLevel.NO_TRAVEL


def test_highest_severity_wins() -> None:
    w = WeatherData(
        forecast_at="2026-11-10T12:00:00Z",
        wind_mph=30.0,
        rain_in_per_hour=0.30,
        snow_in_per_hour=0.1,
        source="test",
        available=True,
    )
    risk = assess_checkpoint_risk(w, load_weight_lb=20_000)
    assert risk.overall == RiskLevel.HIGH
    assert risk.conditions.wind == RiskLevel.MODERATE
    assert risk.conditions.rain == RiskLevel.HIGH
    assert risk.conditions.snow == RiskLevel.LOW
    assert risk.complete is True


def test_missing_weather_values_are_incomplete() -> None:
    w = WeatherData(
        forecast_at="2026-11-10T12:00:00Z",
        wind_mph=None,
        rain_in_per_hour=0.05,
        snow_in_per_hour=None,
        source="test",
        available=True,
    )
    risk = assess_checkpoint_risk(w, load_weight_lb=20_000)
    assert risk.complete is False
    assert risk.conditions.wind is None
    assert risk.conditions.rain == RiskLevel.LOW
    assert risk.conditions.snow is None
    assert risk.overall == RiskLevel.LOW
