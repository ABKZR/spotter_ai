from __future__ import annotations

import logging
from datetime import datetime, timezone

from routing.domain.models import AnalyzedRoute, TripAnalysis
from routing.providers.geocoding_provider import ORSGeocodingProvider
from routing.providers.routing_provider import ORSRoutingProvider
from routing.providers.weather_provider import OpenMeteoWeatherProvider
from routing.services.checkpoint_generator import generate_checkpoints
from routing.services.eta_calculator import calculate_etas
from routing.services.recommendation import calculate_metrics, recommend
from routing.services.weather_enricher import enrich_checkpoints

logger = logging.getLogger(__name__)


async def analyze_trip(
    origin: str,
    destination: str,
    departure_at: str,
    load_weight_lb: float,
    sampling_interval_miles: float = 25.0,
) -> TripAnalysis:
    warnings: list[str] = []

    try:
        dep_dt = datetime.fromisoformat(departure_at)
        if dep_dt.tzinfo is None:
            dep_dt = dep_dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid departure_at: {exc}") from exc

    geocoder = ORSGeocodingProvider()
    try:
        origin_loc = await geocoder.geocode(origin)
    except Exception as exc:
        raise ValueError(f"Failed to geocode origin '{origin}': {exc}") from exc

    try:
        dest_loc = await geocoder.geocode(destination)
    except Exception as exc:
        raise ValueError(f"Failed to geocode destination '{destination}': {exc}") from exc

    import math
    dlat = dest_loc.coordinate.latitude - origin_loc.coordinate.latitude
    dlon = dest_loc.coordinate.longitude - origin_loc.coordinate.longitude
    approx_dist = math.sqrt(dlat**2 + dlon**2) * 69.0
    if approx_dist > 6000:
        raise ValueError(
            f"Origin and destination are {approx_dist:.0f} miles apart. "
            "Please select origin and destination within the North American road network (max: 6,000 miles)."
        )

    router = ORSRoutingProvider()
    try:
        routes = await router.get_routes(
            origin_loc.coordinate,
            dest_loc.coordinate,
            alternatives=3,
        )
    except Exception as exc:
        raise ValueError(f"Failed to compute routes: {exc}") from exc

    if len(routes) < 3:
        warnings.append(f"Only {len(routes)} route(s) available (requested 3).")

    weather_provider = OpenMeteoWeatherProvider()
    analyzed_routes: list[AnalyzedRoute] = []

    for route in routes:
        try:
            checkpoints = generate_checkpoints(route, sampling_interval_miles)
            checkpoints = calculate_etas(checkpoints, route, dep_dt)
            checkpoints = await enrich_checkpoints(
                checkpoints, weather_provider, load_weight_lb
            )
            metrics = calculate_metrics(checkpoints)

            arrival_at = (
                checkpoints[-1].estimated_arrival_at
                if checkpoints
                else dep_dt.isoformat()
            )

            analyzed_routes.append(
                AnalyzedRoute(
                    route=route,
                    checkpoints=checkpoints,
                    metrics=metrics,
                    arrival_at=arrival_at,
                )
            )
        except Exception as exc:
            logger.error("Error analyzing route %s: %s", route.id, exc)
            warnings.append(f"Route '{route.label}' analysis incomplete: {exc}")

    for ar in analyzed_routes:
        if not ar.metrics.complete:
            warnings.append(
                f"Route '{ar.route.label}': weather data incomplete "
                f"({ar.metrics.forecast_coverage_percent:.0f}% coverage)."
            )

    recommendation = recommend(analyzed_routes)

    trip_info = {
        "origin": {
            "label": origin_loc.label,
            "latitude": origin_loc.coordinate.latitude,
            "longitude": origin_loc.coordinate.longitude,
        },
        "destination": {
            "label": dest_loc.label,
            "latitude": dest_loc.coordinate.latitude,
            "longitude": dest_loc.coordinate.longitude,
        },
        "departure_at": dep_dt.isoformat(),
        "load_weight_lb": load_weight_lb,
        "sampling_interval_miles": sampling_interval_miles,
    }

    return TripAnalysis(
        trip=trip_info,
        recommendation=recommendation,
        routes=analyzed_routes,
        warnings=warnings,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
