"""
API Views for Weather-Aware Truck Routing.

Provides endpoints for:
- POST /api/v1/trips/analyze/ : Main route analysis and risk recommendation
- GET  /api/v1/geocode/suggest/ : Autocomplete for addresses/cities
- POST /api/v1/forecast-corridor/ : Weather risk along corridor for 0–48h slider
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging

from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from routing.api.serializers import (
    ForecastCorridorRequestSerializer,
    TripRequestSerializer,
)
from routing.domain.models import (
    AnalyzedRoute,
    Checkpoint,
    RiskLevel,
    TripAnalysis,
    WeatherData,
)
from routing.domain.risk import assess_checkpoint_risk
from routing.providers.geocoding_provider import ORSGeocodingProvider
from routing.providers.weather_provider import OpenMeteoWeatherProvider
from routing.services.route_planner import analyze_trip

logger = logging.getLogger(__name__)


def _serialize_trip_analysis(analysis: TripAnalysis) -> dict:
    """Transform domain TripAnalysis into API response dictionary."""

    def _risk_name(r: RiskLevel | None) -> str | None:
        return r.name.lower() if r is not None else None

    def _serialize_checkpoint(cp: Checkpoint) -> dict:
        weather_dict = None
        if cp.weather:
            weather_dict = {
                "forecast_at": cp.weather.forecast_at,
                "wind_mph": cp.weather.wind_mph,
                "rain_in_per_hour": cp.weather.rain_in_per_hour,
                "snow_in_per_hour": cp.weather.snow_in_per_hour,
                "source": cp.weather.source,
                "available": cp.weather.available,
            }

        risk_dict = None
        if cp.risk:
            risk_dict = {
                "overall": _risk_name(cp.risk.overall),
                "conditions": {
                    "wind": _risk_name(cp.risk.conditions.wind),
                    "rain": _risk_name(cp.risk.conditions.rain),
                    "snow": _risk_name(cp.risk.conditions.snow),
                },
                "load_adjustments": cp.risk.load_adjustments,
                "complete": cp.risk.complete,
            }

        return {
            "id": cp.id,
            "sequence": cp.sequence,
            "distance_from_origin_miles": cp.distance_from_origin_miles,
            "latitude": cp.latitude,
            "longitude": cp.longitude,
            "estimated_arrival_at": cp.estimated_arrival_at,
            "weather": weather_dict,
            "risk": risk_dict,
        }

    def _serialize_route(ar: AnalyzedRoute) -> dict:
        geojson_coords = [
            [c.longitude, c.latitude] for c in ar.route.geometry
        ]

        return {
            "id": ar.route.id,
            "label": ar.route.label,
            "geometry": {
                "type": "LineString",
                "coordinates": geojson_coords,
            },
            "distance_miles": ar.route.distance_miles,
            "duration_seconds": ar.route.duration_seconds,
            "arrival_at": ar.arrival_at,
            "summary": ar.route.summary,
            "metrics": {
                "severe_miles": ar.metrics.severe_miles,
                "high_miles": ar.metrics.high_miles,
                "average_risk": ar.metrics.average_risk,
                "no_travel_checkpoints": ar.metrics.no_travel_checkpoints,
                "forecast_coverage_percent": ar.metrics.forecast_coverage_percent,
                "complete": ar.metrics.complete,
            },
            "checkpoints": [_serialize_checkpoint(cp) for cp in ar.checkpoints],
        }

    recommendation_dict = None
    if analysis.recommendation:
        recommendation_dict = {
            "route_id": analysis.recommendation.route_id,
            "status": analysis.recommendation.status,
            "reason": analysis.recommendation.reason,
        }

    return {
        "trip": analysis.trip,
        "recommendation": recommendation_dict,
        "routes": [_serialize_route(r) for r in analysis.routes],
        "warnings": analysis.warnings,
        "generated_at": analysis.generated_at,
    }


class AnalyzeTripView(APIView):
    """Analyze a proposed truck trip across 3 route options with weather risk."""

    def post(self, request: Request) -> Response:
        serializer = TripRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid trip parameters provided.",
                        "details": serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            analysis = async_to_sync(analyze_trip)(
                origin=data["origin"],
                destination=data["destination"],
                departure_at=data["departure_at"],
                load_weight_lb=data["load_weight_lb"],
                sampling_interval_miles=float(data["sampling_interval_miles"]),
            )
            response_data = _serialize_trip_analysis(analysis)
            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as exc:
            logger.warning("Trip analysis validation/processing error: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "TRIP_ANALYSIS_FAILED",
                        "message": str(exc),
                        "details": {},
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Exception as exc:
            logger.exception("Unexpected error during trip analysis")
            return Response(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An error occurred while calculating route options. Please try again.",
                        "details": {},
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GeocodeSuggestView(APIView):
    """Provide address/city autocomplete suggestions."""

    def get(self, request: Request) -> Response:
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response([], status=status.HTTP_200_OK)

        geocoder = ORSGeocodingProvider()
        try:
            results = async_to_sync(geocoder.autocomplete)(query)
            return Response(results, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.warning("Geocode autocomplete error: %s", exc)
            return Response([], status=status.HTTP_200_OK)


class ForecastCorridorView(APIView):
    """Calculate weather risk at corridor checkpoints at a specific hourly offset (0–48h)."""

    def post(self, request: Request) -> Response:
        serializer = ForecastCorridorRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid corridor parameters.",
                        "details": serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        checkpoints_data = data["checkpoints"]
        departure_str = data["departure_at"]
        hours = data["hours"]
        load_weight_lb = data["load_weight_lb"]

        try:
            dep_dt = datetime.fromisoformat(departure_str)
            if dep_dt.tzinfo is None:
                dep_dt = dep_dt.replace(tzinfo=timezone.utc)
            target_time = dep_dt + timedelta(hours=hours)
            target_iso = target_time.isoformat()
        except Exception as exc:
            return Response(
                {
                    "error": {
                        "code": "INVALID_TIMESTAMP",
                        "message": str(exc),
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        weather_provider = OpenMeteoWeatherProvider()

        async def _assess_corridor():
            reqs = [
                (float(cp["latitude"]), float(cp["longitude"]), target_iso)
                for cp in checkpoints_data
            ]
            forecasts = await weather_provider.get_forecasts_batch(reqs)

            results = []
            for i, cp_item in enumerate(checkpoints_data):
                lat = float(cp_item["latitude"])
                lon = float(cp_item["longitude"])
                cp_id = cp_item.get("id", "")
                seq = cp_item.get("sequence", 0)
                weather = forecasts[i] if i < len(forecasts) else WeatherData(
                    forecast_at=target_iso,
                    wind_mph=None,
                    rain_in_per_hour=None,
                    snow_in_per_hour=None,
                    source="open-meteo",
                    available=False,
                )
                risk = assess_checkpoint_risk(weather, load_weight_lb)
                results.append({
                    "id": cp_id,
                    "sequence": seq,
                    "latitude": lat,
                    "longitude": lon,
                    "target_time": target_iso,
                    "overall_risk": risk.overall.name.lower(),
                    "wind_risk": risk.conditions.wind.name.lower() if risk.conditions.wind else None,
                    "rain_risk": risk.conditions.rain.name.lower() if risk.conditions.rain else None,
                    "snow_risk": risk.conditions.snow.name.lower() if risk.conditions.snow else None,
                    "wind_mph": weather.wind_mph,
                    "rain_in_per_hour": weather.rain_in_per_hour,
                    "snow_in_per_hour": weather.snow_in_per_hour,
                    "load_adjustments": risk.load_adjustments,
                    "complete": risk.complete,
                })
            return results

        corridor_results = async_to_sync(_assess_corridor)()

        return Response(
            {
                "hours_offset": hours,
                "target_time": target_iso,
                "points": corridor_results,
            },
            status=status.HTTP_200_OK,
        )
