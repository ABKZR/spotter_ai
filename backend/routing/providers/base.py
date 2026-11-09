"""
Abstract base classes for external data providers.

These define the contracts that concrete implementations must satisfy.
"""

from __future__ import annotations

import abc

from routing.domain.models import Coordinate, Location, Route, WeatherData


class GeocodingProvider(abc.ABC):
    """Resolve human-readable addresses to geographic coordinates."""

    @abc.abstractmethod
    async def geocode(self, address: str) -> Location:
        """Return the best-matching :class:`Location` for *address*."""

    @abc.abstractmethod
    async def autocomplete(self, query: str) -> list[dict]:
        """Return autocomplete suggestions for *query*."""


class RoutingProvider(abc.ABC):
    """Compute driving routes between two coordinates."""

    @abc.abstractmethod
    async def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        alternatives: int = 3,
    ) -> list[Route]:
        """Return up to *alternatives* route options."""


class WeatherProvider(abc.ABC):
    """Retrieve weather forecasts for a geographic point and time."""

    @abc.abstractmethod
    async def get_forecast(
        self,
        lat: float,
        lon: float,
        forecast_time: str,
    ) -> WeatherData:
        """Return the forecast closest to *forecast_time* at (lat, lon)."""
