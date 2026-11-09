from unittest.mock import patch
import pytest
from rest_framework.test import APIClient

from routing.domain.models import (
    Coordinate,
    Location,
    Route,
    RouteSegment,
    WeatherData,
)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_missing_fields_return_400(client: APIClient) -> None:
    resp = client.post("/api/v1/trips/analyze/", {}, format="json")
    assert resp.status_code == 400
    assert "error" in resp.data
    assert resp.data["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_load_weight_returns_400(client: APIClient) -> None:
    payload = {
        "origin": "Chicago, IL",
        "destination": "Detroit, MI",
        "departure_at": "2026-11-10T08:00:00Z",
        "load_weight_lb": -500,
        "sampling_interval_miles": 25,
    }
    resp = client.post("/api/v1/trips/analyze/", payload, format="json")
    assert resp.status_code == 400
    assert "load_weight_lb" in resp.data["error"]["details"]


def test_invalid_interval_returns_400(client: APIClient) -> None:
    payload = {
        "origin": "Chicago, IL",
        "destination": "Detroit, MI",
        "departure_at": "2026-11-10T08:00:00Z",
        "load_weight_lb": 32000,
        "sampling_interval_miles": 15,
    }
    resp = client.post("/api/v1/trips/analyze/", payload, format="json")
    assert resp.status_code == 400
    assert "sampling_interval_miles" in resp.data["error"]["details"]


def test_identical_origin_and_destination_returns_400(client: APIClient) -> None:
    payload = {
        "origin": "Chicago, IL",
        "destination": "Chicago, IL",
        "departure_at": "2026-11-10T08:00:00Z",
        "load_weight_lb": 32000,
        "sampling_interval_miles": 25,
    }
    resp = client.post("/api/v1/trips/analyze/", payload, format="json")
    assert resp.status_code == 400
    assert "destination" in resp.data["error"]["details"]


def test_missing_timezone_returns_400(client: APIClient) -> None:
    payload = {
        "origin": "Chicago, IL",
        "destination": "Detroit, MI",
        "departure_at": "2026-11-10T08:00:00",
        "load_weight_lb": 32000,
        "sampling_interval_miles": 25,
    }
    resp = client.post("/api/v1/trips/analyze/", payload, format="json")
    assert resp.status_code == 400
    assert "departure_at" in resp.data["error"]["details"]


@pytest.mark.django_db
def test_successful_analysis_endpoint(client: APIClient) -> None:
    payload = {
        "origin": "Chicago, IL",
        "destination": "Detroit, MI",
        "departure_at": "2026-11-10T08:00:00Z",
        "load_weight_lb": 32000,
        "sampling_interval_miles": 50,
    }

    c1, c2 = Coordinate(41.8781, -87.6298), Coordinate(42.3314, -83.0458)
    mock_routes = [
        Route(
            id=f"route-{i}",
            label=f"Route {chr(65+i)}",
            geometry=[c1, Coordinate(42.0, -85.0), c2],
            distance_miles=280.0,
            duration_seconds=16000.0,
            segments=[
                RouteSegment(c1, c2, 280.0, 16000.0, 280.0, 16000.0)
            ],
            summary="280 mi",
        )
        for i in range(3)
    ]

    with patch("routing.services.route_planner.ORSGeocodingProvider.geocode") as mock_geo, \
         patch("routing.services.route_planner.ORSRoutingProvider.get_routes") as mock_route, \
         patch("routing.services.route_planner.OpenMeteoWeatherProvider.get_forecast") as mock_weather:

        mock_geo.side_effect = [
            Location("Chicago, IL", c1),
            Location("Detroit, MI", c2),
        ]
        mock_route.return_value = mock_routes
        mock_weather.return_value = WeatherData(
            forecast_at="2026-11-10T08:00:00Z",
            wind_mph=20.0,
            rain_in_per_hour=0.02,
            snow_in_per_hour=0.0,
            source="mock",
            available=True,
        )

        resp = client.post("/api/v1/trips/analyze/", payload, format="json")
        assert resp.status_code == 200
        data = resp.data

        assert "trip" in data
        assert "recommendation" in data
        assert data["recommendation"]["status"] == "recommended"
        assert len(data["routes"]) == 3

        first_route = data["routes"][0]
        assert first_route["geometry"]["type"] == "LineString"
        assert len(first_route["geometry"]["coordinates"]) >= 2
        assert len(first_route["checkpoints"]) >= 2
        assert "weather" in first_route["checkpoints"][0]
        assert "risk" in first_route["checkpoints"][0]


def test_forecast_corridor_endpoint(client: APIClient) -> None:
    payload = {
        "checkpoints": [
            {"id": "cp1", "sequence": 0, "latitude": 41.8781, "longitude": -87.6298},
            {"id": "cp2", "sequence": 1, "latitude": 42.3314, "longitude": -83.0458},
        ],
        "departure_at": "2026-11-10T08:00:00Z",
        "hours": 12,
        "load_weight_lb": 32000,
    }

    with patch("routing.api.views.OpenMeteoWeatherProvider.get_forecast") as mock_weather:
        mock_weather.return_value = WeatherData(
            forecast_at="2026-11-10T20:00:00Z",
            wind_mph=28.0,
            rain_in_per_hour=0.15,
            snow_in_per_hour=0.0,
            source="mock",
            available=True,
        )

        resp = client.post("/api/v1/forecast-corridor/", payload, format="json")
        assert resp.status_code == 200
        assert resp.data["hours_offset"] == 12
        assert len(resp.data["points"]) == 2
        p1 = resp.data["points"][0]
        assert p1["overall_risk"] == "moderate"
