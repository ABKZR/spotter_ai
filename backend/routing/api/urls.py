"""
URL configuration for the routing API.
"""

from django.urls import path

from routing.api.views import (
    AnalyzeTripView,
    ForecastCorridorView,
    GeocodeSuggestView,
)

urlpatterns = [
    path("trips/analyze/", AnalyzeTripView.as_view(), name="trips-analyze"),
    path("geocode/suggest/", GeocodeSuggestView.as_view(), name="geocode-suggest"),
    path("forecast-corridor/", ForecastCorridorView.as_view(), name="forecast-corridor"),
]
