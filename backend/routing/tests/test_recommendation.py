from routing.domain.models import (
    AnalyzedRoute,
    Coordinate,
    Route,
    RouteMetrics,
)
from routing.services.recommendation import recommend


def _make_analyzed_route(
    route_id: str,
    label: str,
    severe_miles: float,
    high_miles: float,
    average_risk: float,
    duration_seconds: float,
    no_travel_checkpoints: int = 0,
) -> AnalyzedRoute:
    r = Route(
        id=route_id,
        label=label,
        geometry=[Coordinate(40.0, -80.0), Coordinate(41.0, -80.0)],
        distance_miles=100.0,
        duration_seconds=duration_seconds,
        segments=[],
        summary="Test",
    )
    metrics = RouteMetrics(
        severe_miles=severe_miles,
        high_miles=high_miles,
        average_risk=average_risk,
        no_travel_checkpoints=no_travel_checkpoints,
        forecast_coverage_percent=100.0,
        complete=True,
    )
    return AnalyzedRoute(
        route=r,
        checkpoints=[],
        metrics=metrics,
        arrival_at="2026-11-10T12:00:00Z",
    )


def test_fewer_severe_miles_wins_even_if_longer_duration() -> None:
    fast_dangerous = _make_analyzed_route(
        "r1", "Fast Route", severe_miles=10.0, high_miles=0.0, average_risk=1.5, duration_seconds=3600.0
    )
    slow_safe = _make_analyzed_route(
        "r2", "Safe Route", severe_miles=0.0, high_miles=5.0, average_risk=1.2, duration_seconds=5400.0
    )

    rec = recommend([fast_dangerous, slow_safe])
    assert rec is not None
    assert rec.route_id == "r2"
    assert rec.status == "recommended"


def test_severe_tie_broken_by_high_miles() -> None:
    route_a = _make_analyzed_route(
        "ra", "Route A", severe_miles=0.0, high_miles=15.0, average_risk=1.5, duration_seconds=3600.0
    )
    route_b = _make_analyzed_route(
        "rb", "Route B", severe_miles=0.0, high_miles=5.0, average_risk=1.2, duration_seconds=4000.0
    )

    rec = recommend([route_a, route_b])
    assert rec is not None
    assert rec.route_id == "rb"


def test_severe_and_high_tie_broken_by_average_risk() -> None:
    route_a = _make_analyzed_route(
        "ra", "Route A", severe_miles=0.0, high_miles=5.0, average_risk=1.2, duration_seconds=3600.0
    )
    route_b = _make_analyzed_route(
        "rb", "Route B", severe_miles=0.0, high_miles=5.0, average_risk=0.8, duration_seconds=4000.0
    )

    rec = recommend([route_a, route_b])
    assert rec is not None
    assert rec.route_id == "rb"


def test_all_risk_equal_broken_by_duration() -> None:
    route_a = _make_analyzed_route(
        "ra", "Route A", severe_miles=0.0, high_miles=5.0, average_risk=1.0, duration_seconds=3600.0
    )
    route_b = _make_analyzed_route(
        "rb", "Route B", severe_miles=0.0, high_miles=5.0, average_risk=1.0, duration_seconds=4200.0
    )

    rec = recommend([route_a, route_b])
    assert rec is not None
    assert rec.route_id == "ra"


def test_no_travel_route_is_disqualified() -> None:
    no_travel_route = _make_analyzed_route(
        "r_bad", "Dangerous Route", severe_miles=0.0, high_miles=0.0, average_risk=0.5,
        duration_seconds=3000.0, no_travel_checkpoints=1
    )
    eligible_route = _make_analyzed_route(
        "r_ok", "Okay Route", severe_miles=5.0, high_miles=10.0, average_risk=1.5,
        duration_seconds=5000.0, no_travel_checkpoints=0
    )

    rec = recommend([no_travel_route, eligible_route])
    assert rec is not None
    assert rec.route_id == "r_ok"
    assert rec.status == "recommended"


def test_all_routes_no_travel_yields_no_suitable_route() -> None:
    r1 = _make_analyzed_route("r1", "Route 1", 0, 0, 0, 3600, no_travel_checkpoints=2)
    r2 = _make_analyzed_route("r2", "Route 2", 0, 0, 0, 3800, no_travel_checkpoints=1)

    rec = recommend([r1, r2])
    assert rec is not None
    assert rec.status == "no_suitable_route"
