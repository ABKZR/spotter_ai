from __future__ import annotations

import math
import uuid

from routing.domain.models import Checkpoint, Coordinate, Route

_EARTH_RADIUS_MILES = 3958.8


def _haversine_miles(a: Coordinate, b: Coordinate) -> float:
    lat1, lon1 = math.radians(a.latitude), math.radians(a.longitude)
    lat2, lon2 = math.radians(b.latitude), math.radians(b.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_MILES * math.asin(math.sqrt(h))


def _interpolate(a: Coordinate, b: Coordinate, fraction: float) -> Coordinate:
    if fraction <= 0:
        return a
    if fraction >= 1:
        return b
    lat = a.latitude + (b.latitude - a.latitude) * fraction
    lon = a.longitude + (b.longitude - a.longitude) * fraction
    return Coordinate(latitude=lat, longitude=lon)


def generate_checkpoints(
    route: Route,
    sampling_interval_miles: float,
) -> list[Checkpoint]:
    """Generate distance-based checkpoints along the route geometry."""
    geometry = route.geometry
    if len(geometry) < 2:
        coord = geometry[0] if geometry else Coordinate(0, 0)
        return [
            Checkpoint(
                id=str(uuid.uuid4()),
                sequence=0,
                distance_from_origin_miles=0.0,
                latitude=coord.latitude,
                longitude=coord.longitude,
                estimated_arrival_at="",
            )
        ]

    seg_distances: list[float] = []
    cumulative: list[float] = [0.0]
    for i in range(1, len(geometry)):
        d = _haversine_miles(geometry[i - 1], geometry[i])
        seg_distances.append(d)
        cumulative.append(cumulative[-1] + d)

    total_polyline_miles = cumulative[-1]
    total_route_miles = (
        route.distance_miles if route.distance_miles > 0 else total_polyline_miles
    )
    if total_route_miles <= 0:
        total_route_miles = total_polyline_miles

    scale = total_route_miles / total_polyline_miles if total_polyline_miles > 0 else 1.0

    target_distances_route: list[float] = [0.0]
    d = sampling_interval_miles
    while d < total_route_miles:
        target_distances_route.append(d)
        d += sampling_interval_miles

    eps = 1e-6
    if (
        not target_distances_route
        or abs(target_distances_route[-1] - total_route_miles) > eps
    ):
        target_distances_route.append(total_route_miles)

    target_distances_poly = [t / scale for t in target_distances_route]
    checkpoints: list[Checkpoint] = []

    for seq, (target_poly, target_route) in enumerate(
        zip(target_distances_poly, target_distances_route)
    ):
        coord = _find_point_at_distance(
            geometry, cumulative, target_poly, total_polyline_miles
        )
        checkpoints.append(
            Checkpoint(
                id=str(uuid.uuid4()),
                sequence=seq,
                distance_from_origin_miles=round(target_route, 4),
                latitude=coord.latitude,
                longitude=coord.longitude,
                estimated_arrival_at="",
            )
        )

    return checkpoints


def _find_point_at_distance(
    geometry: list[Coordinate],
    cumulative: list[float],
    target_dist: float,
    total_dist: float,
) -> Coordinate:
    if target_dist <= 0:
        return geometry[0]
    if target_dist >= total_dist:
        return geometry[-1]

    lo, hi = 0, len(cumulative) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if cumulative[mid] <= target_dist:
            lo = mid
        else:
            hi = mid

    seg_start_dist = cumulative[lo]
    seg_end_dist = cumulative[hi]
    seg_len = seg_end_dist - seg_start_dist

    if seg_len <= 0:
        return geometry[lo]

    fraction = (target_dist - seg_start_dist) / seg_len
    return _interpolate(geometry[lo], geometry[hi], fraction)
