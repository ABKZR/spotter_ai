from datetime import datetime, timezone

from routing.domain.models import Checkpoint, Coordinate, Route, RouteSegment
from routing.services.eta_calculator import calculate_etas


def test_first_checkpoint_eta_equals_departure() -> None:
    departure = datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc)
    coords = [Coordinate(40.0, -80.0), Coordinate(41.0, -80.0)]
    route = Route(
        id="r1",
        label="R1",
        geometry=coords,
        distance_miles=60.0,
        duration_seconds=3600.0,
        segments=[
            RouteSegment(
                start=coords[0],
                end=coords[1],
                distance_miles=60.0,
                duration_seconds=3600.0,
                cumulative_distance_miles=60.0,
                cumulative_duration_seconds=3600.0,
            )
        ],
        summary="60 mi",
    )
    checkpoints = [
        Checkpoint("cp0", 0, 0.0, 40.0, -80.0, ""),
        Checkpoint("cp1", 1, 30.0, 40.5, -80.0, ""),
        Checkpoint("cp2", 2, 60.0, 41.0, -80.0, ""),
    ]

    calculated = calculate_etas(checkpoints, route, departure)

    assert calculated[0].estimated_arrival_at == departure.isoformat()
    dt1 = datetime.fromisoformat(calculated[1].estimated_arrival_at)
    assert (dt1 - departure).total_seconds() == 1800.0
    dt2 = datetime.fromisoformat(calculated[2].estimated_arrival_at)
    assert (dt2 - departure).total_seconds() == 3600.0


def test_eta_monotonicity() -> None:
    departure = datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc)
    coords = [Coordinate(40.0, -80.0), Coordinate(42.0, -80.0)]
    route = Route(
        id="r1",
        label="R1",
        geometry=coords,
        distance_miles=100.0,
        duration_seconds=7200.0,
        segments=[
            RouteSegment(
                start=coords[0],
                end=coords[1],
                distance_miles=100.0,
                duration_seconds=7200.0,
                cumulative_distance_miles=100.0,
                cumulative_duration_seconds=7200.0,
            )
        ],
        summary="100 mi",
    )
    checkpoints = [
        Checkpoint(f"cp{i}", i, i * 20.0, 40.0 + i * 0.4, -80.0, "")
        for i in range(6)
    ]
    calculated = calculate_etas(checkpoints, route, departure)

    times = [datetime.fromisoformat(cp.estimated_arrival_at) for cp in calculated]
    for i in range(len(times) - 1):
        assert times[i + 1] > times[i]
