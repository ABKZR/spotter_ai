import pytest

from routing.domain.models import Coordinate, Route, RouteSegment
from routing.services.checkpoint_generator import generate_checkpoints


def _make_dummy_route(distance_miles: float, num_points: int = 10) -> Route:
    deg_span = distance_miles / 69.0
    coords = [
        Coordinate(latitude=40.0 + (i / (num_points - 1)) * deg_span, longitude=-80.0)
        for i in range(num_points)
    ]
    segments = [
        RouteSegment(
            start=coords[i - 1],
            end=coords[i],
            distance_miles=distance_miles / (num_points - 1),
            duration_seconds=3600.0 / (num_points - 1),
            cumulative_distance_miles=(i / (num_points - 1)) * distance_miles,
            cumulative_duration_seconds=(i / (num_points - 1)) * 3600.0,
        )
        for i in range(1, num_points)
    ]
    return Route(
        id="test-route",
        label="Test Route",
        geometry=coords,
        distance_miles=distance_miles,
        duration_seconds=3600.0,
        segments=segments,
        summary="Test",
    )


def test_checkpoint_spacing_63_miles_at_25_miles() -> None:
    route = _make_dummy_route(63.0)
    checkpoints = generate_checkpoints(route, sampling_interval_miles=25.0)

    distances = [cp.distance_from_origin_miles for cp in checkpoints]
    assert len(distances) == 4
    assert distances[0] == 0.0
    assert pytest.approx(distances[1], rel=1e-2) == 25.0
    assert pytest.approx(distances[2], rel=1e-2) == 50.0
    assert pytest.approx(distances[3], rel=1e-2) == 63.0


def test_checkpoint_spacing_100_miles_at_50_miles_no_duplicate() -> None:
    route = _make_dummy_route(100.0)
    checkpoints = generate_checkpoints(route, sampling_interval_miles=50.0)

    distances = [cp.distance_from_origin_miles for cp in checkpoints]
    assert len(distances) == 3
    assert distances[0] == 0.0
    assert pytest.approx(distances[1], rel=1e-2) == 50.0
    assert pytest.approx(distances[2], rel=1e-2) == 100.0


def test_route_shorter_than_interval() -> None:
    route = _make_dummy_route(15.0)
    checkpoints = generate_checkpoints(route, sampling_interval_miles=25.0)

    distances = [cp.distance_from_origin_miles for cp in checkpoints]
    assert len(distances) == 2
    assert distances[0] == 0.0
    assert pytest.approx(distances[1], rel=1e-2) == 15.0


def test_checkpoints_are_monotonically_ordered() -> None:
    route = _make_dummy_route(250.0, num_points=30)
    checkpoints = generate_checkpoints(route, sampling_interval_miles=25.0)

    for i in range(len(checkpoints) - 1):
        assert (
            checkpoints[i + 1].distance_from_origin_miles
            > checkpoints[i].distance_from_origin_miles
        )
