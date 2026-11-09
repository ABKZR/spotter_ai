from __future__ import annotations

import math

from routing.domain.models import (
    CheckpointRisk,
    ConditionRisk,
    RiskLevel,
    WeatherData,
)


def classify_wind(wind_mph: float) -> RiskLevel:
    """Classify wind risk based on sustained speed in mph."""
    if math.isnan(wind_mph):
        raise ValueError("wind_mph must not be NaN")
    if wind_mph < 0:
        wind_mph = 0.0
    if wind_mph < 25:
        return RiskLevel.LOW
    if wind_mph < 35:
        return RiskLevel.MODERATE
    if wind_mph < 45:
        return RiskLevel.HIGH
    if wind_mph < 55:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def classify_rain(rain_in_per_hour: float) -> RiskLevel:
    """Classify rain risk based on precipitation intensity in inches/hour."""
    if math.isnan(rain_in_per_hour):
        raise ValueError("rain_in_per_hour must not be NaN")
    if rain_in_per_hour < 0:
        rain_in_per_hour = 0.0
    if rain_in_per_hour < 0.10:
        return RiskLevel.LOW
    if rain_in_per_hour < 0.25:
        return RiskLevel.MODERATE
    if rain_in_per_hour < 0.50:
        return RiskLevel.HIGH
    if rain_in_per_hour <= 1.00:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def classify_snow(snow_in_per_hour: float) -> RiskLevel:
    """Classify snow risk based on snowfall rate in inches/hour."""
    if math.isnan(snow_in_per_hour):
        raise ValueError("snow_in_per_hour must not be NaN")
    if snow_in_per_hour < 0:
        snow_in_per_hour = 0.0
    if snow_in_per_hour < 0.5:
        return RiskLevel.LOW
    if snow_in_per_hour < 1.0:
        return RiskLevel.MODERATE
    if snow_in_per_hour < 2.0:
        return RiskLevel.HIGH
    if snow_in_per_hour <= 3.0:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def apply_load_rules(
    wind_risk: RiskLevel,
    wind_mph: float,
    load_weight_lb: float,
) -> tuple[RiskLevel, list[str]]:
    """Evaluate vehicle weight constraints against current wind velocity."""
    adjusted = wind_risk
    adjustments: list[str] = []

    if 45 <= wind_mph < 55 and load_weight_lb > 30_000:
        candidate = RiskLevel.NO_TRAVEL
        if candidate > adjusted:
            adjusted = candidate
            adjustments.append(
                f"Wind {wind_mph:.0f} mph with load >{30_000:,} lb: No Travel"
            )

    if 35 <= wind_mph < 45 and load_weight_lb > 40_000:
        candidate = RiskLevel.SEVERE
        if candidate > adjusted:
            adjusted = candidate
            adjustments.append(
                f"Wind {wind_mph:.0f} mph with load >{40_000:,} lb: Severe"
            )

    return adjusted, adjustments


def assess_checkpoint_risk(
    weather: WeatherData,
    load_weight_lb: float,
) -> CheckpointRisk:
    """Compute overall checkpoint risk from all available weather metrics and load."""
    wind_risk: RiskLevel | None = None
    rain_risk: RiskLevel | None = None
    snow_risk: RiskLevel | None = None
    load_adjustments: list[str] = []
    complete = True

    if weather.wind_mph is not None:
        wind_risk = classify_wind(weather.wind_mph)
        wind_risk, load_adjustments = apply_load_rules(
            wind_risk, weather.wind_mph, load_weight_lb
        )
    else:
        complete = False

    if weather.rain_in_per_hour is not None:
        rain_risk = classify_rain(weather.rain_in_per_hour)
    else:
        complete = False

    if weather.snow_in_per_hour is not None:
        snow_risk = classify_snow(weather.snow_in_per_hour)
    else:
        complete = False

    known_risks = [r for r in (wind_risk, rain_risk, snow_risk) if r is not None]
    if known_risks:
        overall = max(known_risks)
    else:
        overall = RiskLevel.LOW
        complete = False

    conditions = ConditionRisk(wind=wind_risk, rain=rain_risk, snow=snow_risk)

    return CheckpointRisk(
        overall=overall,
        conditions=conditions,
        load_adjustments=load_adjustments,
        complete=complete,
    )
