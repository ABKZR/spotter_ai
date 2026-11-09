from __future__ import annotations

import logging

from routing.domain.models import Checkpoint, WeatherData
from routing.domain.risk import assess_checkpoint_risk
from routing.providers.weather_provider import OpenMeteoWeatherProvider

logger = logging.getLogger(__name__)


async def enrich_checkpoints(
    checkpoints: list[Checkpoint],
    weather_provider: OpenMeteoWeatherProvider,
    load_weight_lb: float,
) -> list[Checkpoint]:
    if not checkpoints:
        return checkpoints

    requests = [
        (cp.latitude, cp.longitude, cp.estimated_arrival_at)
        for cp in checkpoints
    ]

    forecasts = await weather_provider.get_forecasts_batch(requests)

    for i, cp in enumerate(checkpoints):
        weather = forecasts[i] if i < len(forecasts) else None
        if not weather:
            weather = WeatherData(
                forecast_at=cp.estimated_arrival_at,
                wind_mph=None,
                rain_in_per_hour=None,
                snow_in_per_hour=None,
                source="open-meteo",
                available=False,
            )

        cp.weather = weather
        cp.risk = assess_checkpoint_risk(weather, load_weight_lb)

    return checkpoints
