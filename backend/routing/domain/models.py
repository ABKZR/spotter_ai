from __future__ import annotations

import enum
from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Location:
    label: str
    coordinate: Coordinate


@dataclass(frozen=True)
class RouteSegment:
    start: Coordinate
    end: Coordinate
    distance_miles: float
    duration_seconds: float
    cumulative_distance_miles: float
    cumulative_duration_seconds: float


@dataclass(frozen=True)
class Route:
    id: str
    label: str
    geometry: list[Coordinate]
    distance_miles: float
    duration_seconds: float
    segments: list[RouteSegment]
    summary: str


@dataclass
class WeatherData:
    forecast_at: str
    wind_mph: float | None
    rain_in_per_hour: float | None
    snow_in_per_hour: float | None
    source: str
    available: bool


class RiskLevel(enum.Enum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4

    @property
    def score(self) -> int:
        return self.value

    def __lt__(self, other: RiskLevel) -> bool:
        if not isinstance(other, RiskLevel):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: RiskLevel) -> bool:
        if not isinstance(other, RiskLevel):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: RiskLevel) -> bool:
        if not isinstance(other, RiskLevel):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: RiskLevel) -> bool:
        if not isinstance(other, RiskLevel):
            return NotImplemented
        return self.value >= other.value


@dataclass
class ConditionRisk:
    wind: RiskLevel | None
    rain: RiskLevel | None
    snow: RiskLevel | None


@dataclass
class CheckpointRisk:
    overall: RiskLevel
    conditions: ConditionRisk
    load_adjustments: list[str]
    complete: bool


@dataclass
class Checkpoint:
    id: str
    sequence: int
    distance_from_origin_miles: float
    latitude: float
    longitude: float
    estimated_arrival_at: str
    weather: WeatherData | None = None
    risk: CheckpointRisk | None = None


@dataclass
class RouteMetrics:
    severe_miles: float
    high_miles: float
    average_risk: float
    no_travel_checkpoints: int
    forecast_coverage_percent: float
    complete: bool


@dataclass
class AnalyzedRoute:
    route: Route
    checkpoints: list[Checkpoint]
    metrics: RouteMetrics
    arrival_at: str


@dataclass
class Recommendation:
    route_id: str
    status: str
    reason: list[str]


@dataclass
class TripAnalysis:
    trip: dict
    recommendation: Recommendation | None
    routes: list[AnalyzedRoute]
    warnings: list[str]
    generated_at: str
