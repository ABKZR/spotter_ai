from __future__ import annotations

from datetime import datetime
from rest_framework import serializers


class CoordinateSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class LocationSerializer(serializers.Serializer):
    label = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class WeatherDataSerializer(serializers.Serializer):
    forecast_at = serializers.CharField()
    wind_mph = serializers.FloatField(allow_null=True)
    rain_in_per_hour = serializers.FloatField(allow_null=True)
    snow_in_per_hour = serializers.FloatField(allow_null=True)
    source = serializers.CharField()
    available = serializers.BooleanField()


class ConditionRiskSerializer(serializers.Serializer):
    wind = serializers.CharField(allow_null=True)
    rain = serializers.CharField(allow_null=True)
    snow = serializers.CharField(allow_null=True)


class CheckpointRiskSerializer(serializers.Serializer):
    overall = serializers.CharField()
    conditions = ConditionRiskSerializer()
    load_adjustments = serializers.ListField(child=serializers.CharField())
    complete = serializers.BooleanField()


class CheckpointSerializer(serializers.Serializer):
    id = serializers.CharField()
    sequence = serializers.IntegerField()
    distance_from_origin_miles = serializers.FloatField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    estimated_arrival_at = serializers.CharField()
    weather = WeatherDataSerializer(allow_null=True)
    risk = CheckpointRiskSerializer(allow_null=True)


class RouteGeometrySerializer(serializers.Serializer):
    type = serializers.CharField(default="LineString")
    coordinates = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)
    )


class RouteMetricsSerializer(serializers.Serializer):
    severe_miles = serializers.FloatField()
    high_miles = serializers.FloatField()
    average_risk = serializers.FloatField()
    no_travel_checkpoints = serializers.IntegerField()
    forecast_coverage_percent = serializers.FloatField()
    complete = serializers.BooleanField()


class AnalyzedRouteSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    geometry = RouteGeometrySerializer()
    distance_miles = serializers.FloatField()
    duration_seconds = serializers.FloatField()
    arrival_at = serializers.CharField()
    summary = serializers.CharField()
    metrics = RouteMetricsSerializer()
    checkpoints = CheckpointSerializer(many=True)


class RecommendationSerializer(serializers.Serializer):
    route_id = serializers.CharField()
    status = serializers.CharField()
    reason = serializers.ListField(child=serializers.CharField())


class TripInfoSerializer(serializers.Serializer):
    origin = LocationSerializer()
    destination = LocationSerializer()
    departure_at = serializers.CharField()
    load_weight_lb = serializers.FloatField()
    sampling_interval_miles = serializers.FloatField()


class TripAnalysisSerializer(serializers.Serializer):
    trip = TripInfoSerializer()
    recommendation = RecommendationSerializer(allow_null=True)
    routes = AnalyzedRouteSerializer(many=True)
    warnings = serializers.ListField(child=serializers.CharField())
    generated_at = serializers.CharField()


class TripRequestSerializer(serializers.Serializer):
    """Validate incoming trip analysis request."""

    origin = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={"blank": "Origin is required.", "required": "Origin is required."},
    )
    destination = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={"blank": "Destination is required.", "required": "Destination is required."},
    )
    departure_at = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={"blank": "Departure date/time is required.", "required": "Departure date/time is required."},
    )
    load_weight_lb = serializers.FloatField(
        required=True,
        min_value=0.01,
        error_messages={
            "min_value": "Load weight must be a positive number greater than 0.",
            "invalid": "Load weight must be a valid number.",
        },
    )
    sampling_interval_miles = serializers.ChoiceField(
        choices=[10, 25, 50],
        default=25,
        error_messages={"invalid_choice": "Sampling interval must be 10, 25, or 50 miles."},
    )

    def validate_departure_at(self, value: str) -> str:
        """Validate ISO 8601 datetime format with timezone."""
        try:
            dt = datetime.fromisoformat(value)
        except (ValueError, TypeError) as exc:
            raise serializers.ValidationError(
                "Invalid departure date/time format. Use ISO 8601 (e.g., 2026-11-10T08:00:00Z)."
            ) from exc

        if dt.tzinfo is None:
            raise serializers.ValidationError(
                "Departure date/time must include a timezone or UTC offset (e.g. Z or -05:00)."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        """Ensure origin and destination are distinct."""
        origin = attrs.get("origin", "").strip().lower()
        destination = attrs.get("destination", "").strip().lower()
        if origin and destination and origin == destination:
            raise serializers.ValidationError(
                {"destination": "Destination cannot be identical to origin."}
            )
        return attrs


class ForecastCorridorRequestSerializer(serializers.Serializer):
    """Request weather risk at checkpoints for a given hourly offset."""

    checkpoints = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        allow_empty=False,
    )
    departure_at = serializers.CharField(required=True)
    hours = serializers.IntegerField(
        required=True,
        min_value=0,
        max_value=48,
        error_messages={
            "min_value": "Forecast hours must be between 0 and 48.",
            "max_value": "Forecast hours must be between 0 and 48.",
        },
    )
    load_weight_lb = serializers.FloatField(required=True, min_value=0.01)
