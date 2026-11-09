from __future__ import annotations

from routing.domain.models import (
    AnalyzedRoute,
    Checkpoint,
    Recommendation,
    RiskLevel,
    RouteMetrics,
)


def calculate_metrics(checkpoints: list[Checkpoint]) -> RouteMetrics:
    """Compute aggregate risk metrics across all checkpoints on a route."""
    if not checkpoints:
        return RouteMetrics(
            severe_miles=0.0,
            high_miles=0.0,
            average_risk=0.0,
            no_travel_checkpoints=0,
            forecast_coverage_percent=0.0,
            complete=False,
        )

    severe_miles = 0.0
    high_miles = 0.0
    no_travel_count = 0
    complete_count = 0
    total_checkpoints = len(checkpoints)

    weighted_risk_sum = 0.0
    weighted_distance_sum = 0.0

    for i, cp in enumerate(checkpoints):
        risk_level = cp.risk.overall if cp.risk else RiskLevel.LOW
        risk_complete = cp.risk.complete if cp.risk else False

        if risk_complete:
            complete_count += 1

        if risk_level == RiskLevel.NO_TRAVEL:
            no_travel_count += 1

        if i < len(checkpoints) - 1:
            seg_dist = (
                checkpoints[i + 1].distance_from_origin_miles
                - cp.distance_from_origin_miles
            )
        else:
            seg_dist = 0.0

        seg_dist = max(seg_dist, 0.0)

        if risk_level >= RiskLevel.SEVERE:
            severe_miles += seg_dist
        if risk_level >= RiskLevel.HIGH:
            high_miles += seg_dist

        weighted_risk_sum += risk_level.score * seg_dist
        weighted_distance_sum += seg_dist

    average_risk = (
        weighted_risk_sum / weighted_distance_sum
        if weighted_distance_sum > 0
        else 0.0
    )

    forecast_coverage = (
        (complete_count / total_checkpoints) * 100
        if total_checkpoints > 0
        else 0.0
    )

    all_complete = complete_count == total_checkpoints

    return RouteMetrics(
        severe_miles=round(severe_miles, 2),
        high_miles=round(high_miles, 2),
        average_risk=round(average_risk, 4),
        no_travel_checkpoints=no_travel_count,
        forecast_coverage_percent=round(forecast_coverage, 1),
        complete=all_complete,
    )


def _route_sort_key(analyzed: AnalyzedRoute) -> tuple:
    m = analyzed.metrics
    return (
        m.severe_miles,
        m.high_miles,
        m.average_risk,
        analyzed.route.duration_seconds,
        analyzed.route.id,
    )


def rank_routes(routes: list[AnalyzedRoute]) -> list[AnalyzedRoute]:
    return sorted(routes, key=_route_sort_key)


def recommend(routes: list[AnalyzedRoute]) -> Recommendation | None:
    if not routes:
        return None

    ranked = rank_routes(routes)

    eligible = [r for r in ranked if r.metrics.no_travel_checkpoints == 0]
    ineligible = [r for r in ranked if r.metrics.no_travel_checkpoints > 0]

    if not eligible:
        best = ranked[0]
        return Recommendation(
            route_id=best.route.id,
            status="no_suitable_route",
            reason=[
                "All routes contain checkpoints with No Travel conditions.",
                f"Least affected route: {best.route.label} "
                f"({best.metrics.no_travel_checkpoints} No Travel checkpoint(s)).",
            ],
        )

    best = eligible[0]
    reasons = _build_reasons(best, eligible, ineligible)

    return Recommendation(
        route_id=best.route.id,
        status="recommended",
        reason=reasons,
    )


def _build_reasons(
    best: AnalyzedRoute,
    eligible: list[AnalyzedRoute],
    ineligible: list[AnalyzedRoute],
) -> list[str]:
    reasons: list[str] = []

    reasons.append(f"Recommended: {best.route.label} ({best.route.summary}).")

    if ineligible:
        labels = ", ".join(r.route.label for r in ineligible)
        reasons.append(f"Excluded due to No Travel conditions: {labels}.")

    if len(eligible) > 1:
        runner_up = eligible[1]
        bm, rm = best.metrics, runner_up.metrics
        if bm.severe_miles < rm.severe_miles:
            reasons.append(
                f"Fewer severe-weather miles ({bm.severe_miles:.1f} vs {rm.severe_miles:.1f})."
            )
        elif bm.high_miles < rm.high_miles:
            reasons.append(
                f"Fewer high-risk miles ({bm.high_miles:.1f} vs {rm.high_miles:.1f})."
            )
        elif bm.average_risk < rm.average_risk:
            reasons.append(
                f"Lower average risk ({bm.average_risk:.2f} vs {rm.average_risk:.2f})."
            )
        elif best.route.duration_seconds < runner_up.route.duration_seconds:
            reasons.append(
                f"Shorter travel time ({best.route.duration_seconds / 3600:.1f} hr vs "
                f"{runner_up.route.duration_seconds / 3600:.1f} hr)."
            )

    if best.metrics.severe_miles == 0 and best.metrics.high_miles == 0:
        reasons.append("No severe or high-risk segments on this route.")

    return reasons
