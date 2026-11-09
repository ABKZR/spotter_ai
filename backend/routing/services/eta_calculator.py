"""
ETA calculator — estimates arrival time at each checkpoint.

Uses cumulative distance from route segments to interpolate the duration
at each checkpoint's distance, then adds it to the departure time.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from routing.domain.models import Checkpoint, Route


def calculate_etas(
    checkpoints: list[Checkpoint],
    route: Route,
    departure_at: datetime,
) -> list[Checkpoint]:
    """Fill in ``estimated_arrival_at`` for each checkpoint.

    For each checkpoint at distance *d*:
        1. Find the route segment containing *d*.
        2. Interpolate duration within that segment.
        3. Add the interpolated cumulative duration to *departure_at*.

    The first checkpoint (origin) always has ETA = departure_at.
    """
    if not checkpoints:
        return checkpoints

    if departure_at.tzinfo is None:
        departure_at = departure_at.replace(tzinfo=timezone.utc)

    segments = route.segments
    total_distance = route.distance_miles
    total_duration = route.duration_seconds

    for cp in checkpoints:
        d = cp.distance_from_origin_miles
        if d <= 0 or not segments:
            eta = departure_at
        elif total_distance > 0 and d >= total_distance:
            eta = departure_at + timedelta(seconds=total_duration)
        else:
            duration_s = _interpolate_duration(d, segments, total_distance, total_duration)
            eta = departure_at + timedelta(seconds=duration_s)

        cp.estimated_arrival_at = eta.isoformat()

    return checkpoints


def _interpolate_duration(
    distance_miles: float,
    segments: list,
    total_distance: float,
    total_duration: float,
) -> float:
    prev_cum_dist = 0.0
    prev_cum_dur = 0.0

    for seg in segments:
        seg_cum_dist = seg.cumulative_distance_miles
        seg_cum_dur = seg.cumulative_duration_seconds

        if distance_miles <= seg_cum_dist:
            seg_dist = seg_cum_dist - prev_cum_dist
            seg_dur = seg_cum_dur - prev_cum_dur
            if seg_dist <= 0:
                return seg_cum_dur
            fraction = (distance_miles - prev_cum_dist) / seg_dist
            return prev_cum_dur + fraction * seg_dur

        prev_cum_dist = seg_cum_dist
        prev_cum_dur = seg_cum_dur

    if total_distance > 0:
        return (distance_miles / total_distance) * total_duration
    return total_duration
