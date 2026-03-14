"""DataUpdateCoordinator for the AthleticLayer integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    AIR_QUALITY_API_URL,
    CONF_ZONE,
    DOMAIN,
    FORECAST_HOURS,
    UPDATE_INTERVAL_MINUTES,
    WEATHER_API_URL,
)

_LOGGER = logging.getLogger(__name__)

# ── Open-Meteo parameter lists ──────────────────────────────────────

WEATHER_CURRENT_PARAMS = ",".join(
    [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "weather_code",
        "cloud_cover",
        "pressure_msl",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
    ]
)

WEATHER_HOURLY_PARAMS = ",".join(
    [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation_probability",
        "precipitation",
        "rain",
        "weather_code",
        "cloud_cover",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "uv_index",
        "dew_point_2m",
    ]
)

WEATHER_DAILY_PARAMS = "sunrise,sunset"

AIR_QUALITY_CURRENT_PARAMS = ",".join(
    [
        "european_aqi",
        "pm2_5",
        "pm10",
    ]
)

AIR_QUALITY_HOURLY_PARAMS = ",".join(
    [
        "european_aqi",
        "pm2_5",
        "pm10",
        "alder_pollen",
        "birch_pollen",
        "grass_pollen",
        "mugwort_pollen",
        "olive_pollen",
        "ragweed_pollen",
    ]
)


class AthleticLayerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that fetches weather & air-quality data from Open-Meteo."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.config_entry = config_entry

        # Resolve zone → coordinates & name
        zone_entity_id = config_entry.data.get(CONF_ZONE, "zone.home")
        zone_state = hass.states.get(zone_entity_id)
        if zone_state:
            self.latitude: float = zone_state.attributes.get(
                "latitude", hass.config.latitude
            )
            self.longitude: float = zone_state.attributes.get(
                "longitude", hass.config.longitude
            )
            self.location_name: str = zone_state.name or ""
        else:
            self.latitude = hass.config.latitude
            self.longitude = hass.config.longitude
            self.location_name = hass.config.location_name or ""

        self.timezone: str = str(hass.config.time_zone)
        self._session = async_get_clientsession(hass)

    # ── main update ─────────────────────────────────────────────────

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from both Open-Meteo endpoints in parallel."""
        weather_task = self._fetch_weather()
        air_quality_task = self._fetch_air_quality()

        results = await asyncio.gather(
            weather_task, air_quality_task, return_exceptions=True
        )

        weather_data: dict[str, Any] | Exception = results[0]
        air_quality_data: dict[str, Any] | Exception | None = results[1]

        # Weather is critical – bubble up as UpdateFailed
        if isinstance(weather_data, Exception):
            raise UpdateFailed(
                f"Error fetching weather data: {weather_data}"
            ) from weather_data

        # Air-quality is non-critical – log & continue
        if isinstance(air_quality_data, Exception):
            _LOGGER.warning("Error fetching air quality data: %s", air_quality_data)
            air_quality_data = None

        # Pre-compute the current-hour index for each hourly array
        weather_hour_idx = self._find_current_hour_index(
            weather_data.get("hourly", {}).get("time", [])
        )
        aq_hour_idx = (
            self._find_current_hour_index(
                air_quality_data.get("hourly", {}).get("time", [])
            )
            if air_quality_data
            else 0
        )

        rainfall_forecast = self._process_rainfall_forecast(
            weather_data, weather_hour_idx
        )

        return {
            "weather": weather_data,
            "air_quality": air_quality_data,
            "rainfall_forecast": rainfall_forecast,
            "weather_hour_index": weather_hour_idx,
            "air_quality_hour_index": aq_hour_idx,
        }

    # ── API helpers ─────────────────────────────────────────────────

    async def _fetch_weather(self) -> dict[str, Any]:
        """Fetch forecast data from the Open-Meteo weather API."""
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": WEATHER_CURRENT_PARAMS,
            "hourly": WEATHER_HOURLY_PARAMS,
            "daily": WEATHER_DAILY_PARAMS,
            "forecast_hours": FORECAST_HOURS,
            "timezone": "auto",
        }
        async with self._session.get(WEATHER_API_URL, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_air_quality(self) -> dict[str, Any]:
        """Fetch air-quality / pollen data from the Open-Meteo AQ API."""
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": AIR_QUALITY_CURRENT_PARAMS,
            "hourly": AIR_QUALITY_HOURLY_PARAMS,
            "forecast_hours": FORECAST_HOURS,
            "timezone": "auto",
        }
        async with self._session.get(AIR_QUALITY_API_URL, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    # ── data processing helpers ─────────────────────────────────────

    @staticmethod
    def _find_current_hour_index(times: list[str]) -> int:
        """Return the index whose timestamp is closest to (but ≤) now."""
        if not times:
            return 0

        now = datetime.now()
        best_idx = 0
        for i, time_str in enumerate(times):
            try:
                hour_time = datetime.fromisoformat(time_str)
                if hour_time <= now:
                    best_idx = i
                else:
                    break
            except (ValueError, TypeError):
                continue
        return best_idx

    @staticmethod
    def _process_rainfall_forecast(
        weather_data: dict[str, Any],
        current_idx: int,
    ) -> dict[str, Any]:
        """Build an 8-hour rainfall forecast starting from *current_idx*."""
        hourly = weather_data.get("hourly", {})
        times = hourly.get("time", [])
        rain_values = hourly.get("rain", [])
        precip_prob = hourly.get("precipitation_probability", [])

        forecast: list[dict[str, Any]] = []
        total_rain = 0.0

        for i in range(current_idx, min(current_idx + 8, len(times))):
            rain_mm = rain_values[i] if i < len(rain_values) else 0.0
            prob = precip_prob[i] if i < len(precip_prob) else 0
            rain_mm = rain_mm or 0.0
            total_rain += rain_mm
            forecast.append(
                {
                    "time": times[i],
                    "rain_mm": round(rain_mm, 1),
                    "precipitation_probability": prob or 0,
                }
            )

        return {
            "total_mm": round(total_rain, 1),
            "hourly": forecast,
        }
