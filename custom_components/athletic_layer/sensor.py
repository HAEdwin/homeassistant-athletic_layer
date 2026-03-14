"""Sensor platform for the AthleticLayer integration."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    EVENT_CORE_CONFIG_UPDATE,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .advice import AdviceEngine, HourAdvice, WeatherSlice
from .const import (
    ADVICE_LABEL,
    CONF_HEALTH_CONDITIONS,
    CONF_SPORT,
    CONF_USER_ID,
    DEFAULT_LANGUAGE,
    DOMAIN,
    SPORT_NAMES,
    SUPPORTED_LANGUAGES,
    WMO_CODES,
)
from .coordinator import AthleticLayerCoordinator

# ── 16-point compass directions ─────────────────────────────────────

_COMPASS_LABELS = (
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
)


def degrees_to_compass(degrees: float | int | None) -> str | None:
    """Convert degrees (0-360) to a 16-point compass direction."""
    if degrees is None:
        return None
    idx = round(degrees / 22.5) % 16
    return _COMPASS_LABELS[idx]


# ── Sensor entity description with data-path metadata ──────────────


@dataclass(frozen=True, kw_only=True)
class AthleticLayerSensorDescription(SensorEntityDescription):
    """Extended description that knows where the value lives in coordinator data."""

    # Top-level key: "weather" | "air_quality" | "rainfall_forecast"
    source: str = "weather"
    # "current" → data[source]["current"][api_key]
    # "hourly"  → data[source]["hourly"][api_key][current_hour_index]
    # "direct"  → data[source][api_key]
    data_type: str = "current"
    # Key inside the Open-Meteo JSON
    api_key: str = ""
    # For rain_hour sensors: offset from the current hour (1-8)
    hour_offset: int = 0


# ── Entity descriptions ─────────────────────────────────────────────

SENSOR_DESCRIPTIONS: tuple[AthleticLayerSensorDescription, ...] = (
    # ── Current weather ──────────────────────────────────────────
    AthleticLayerSensorDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="weather",
        data_type="current",
        api_key="temperature_2m",
    ),
    AthleticLayerSensorDescription(
        key="feels_like_temperature",
        translation_key="feels_like_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="weather",
        data_type="current",
        api_key="apparent_temperature",
    ),
    AthleticLayerSensorDescription(
        key="weather_condition",
        translation_key="weather_condition",
        device_class=SensorDeviceClass.ENUM,
        options=list(WMO_CODES.values()),
        icon="mdi:weather-partly-cloudy",
        source="weather",
        data_type="current",
        api_key="weather_code",
    ),
    AthleticLayerSensorDescription(
        key="wind_speed",
        translation_key="wind_speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="weather",
        data_type="current",
        api_key="wind_speed_10m",
    ),
    AthleticLayerSensorDescription(
        key="wind_direction",
        translation_key="wind_direction",
        icon="mdi:compass-outline",
        source="weather",
        data_type="current",
        api_key="wind_direction_10m",
    ),
    AthleticLayerSensorDescription(
        key="wind_gusts",
        translation_key="wind_gusts",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="weather",
        data_type="current",
        api_key="wind_gusts_10m",
    ),
    AthleticLayerSensorDescription(
        key="humidity",
        translation_key="humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        source="weather",
        data_type="current",
        api_key="relative_humidity_2m",
    ),
    AthleticLayerSensorDescription(
        key="pressure",
        translation_key="pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="weather",
        data_type="current",
        api_key="pressure_msl",
    ),
    AthleticLayerSensorDescription(
        key="cloud_cover",
        translation_key="cloud_cover",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:cloud",
        source="weather",
        data_type="current",
        api_key="cloud_cover",
    ),
    AthleticLayerSensorDescription(
        key="precipitation",
        translation_key="precipitation",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="weather",
        data_type="current",
        api_key="precipitation",
    ),
    # ── Hourly-derived weather ───────────────────────────────────
    AthleticLayerSensorDescription(
        key="uv_index",
        translation_key="uv_index",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:sun-wireless",
        source="weather",
        data_type="hourly",
        api_key="uv_index",
    ),
    AthleticLayerSensorDescription(
        key="dew_point",
        translation_key="dew_point",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="weather",
        data_type="hourly",
        api_key="dew_point_2m",
    ),
    AthleticLayerSensorDescription(
        key="precipitation_probability",
        translation_key="precipitation_probability",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:weather-rainy",
        source="weather",
        data_type="hourly",
        api_key="precipitation_probability",
    ),
    # ── 8-hour rainfall forecast (total) ──────────────────────────
    AthleticLayerSensorDescription(
        key="rainfall_forecast_8h",
        translation_key="rainfall_forecast_8h",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:weather-pouring",
        source="rainfall_forecast",
        data_type="direct",
        api_key="total_mm",
    ),
    # ── Per-hour rain sensors (h+1 … h+8) are created dynamically ─
    # ── Air quality ──────────────────────────────────────────────
    AthleticLayerSensorDescription(
        key="air_quality_index",
        translation_key="air_quality_index",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:air-filter",
        source="air_quality",
        data_type="current",
        api_key="european_aqi",
    ),
    AthleticLayerSensorDescription(
        key="pm25",
        translation_key="pm25",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="air_quality",
        data_type="current",
        api_key="pm2_5",
    ),
    AthleticLayerSensorDescription(
        key="pm10",
        translation_key="pm10",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.PM10,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        source="air_quality",
        data_type="current",
        api_key="pm10",
    ),
    # ── Pollen (hourly from air-quality endpoint) ────────────────
    AthleticLayerSensorDescription(
        key="pollen_grass",
        translation_key="pollen_grass",
        native_unit_of_measurement="grains/m³",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:grass",
        source="air_quality",
        data_type="hourly",
        api_key="grass_pollen",
    ),
    AthleticLayerSensorDescription(
        key="pollen_birch",
        translation_key="pollen_birch",
        native_unit_of_measurement="grains/m³",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:tree",
        source="air_quality",
        data_type="hourly",
        api_key="birch_pollen",
    ),
    AthleticLayerSensorDescription(
        key="pollen_alder",
        translation_key="pollen_alder",
        native_unit_of_measurement="grains/m³",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:tree",
        source="air_quality",
        data_type="hourly",
        api_key="alder_pollen",
    ),
    AthleticLayerSensorDescription(
        key="pollen_mugwort",
        translation_key="pollen_mugwort",
        native_unit_of_measurement="grains/m³",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flower-pollen",
        source="air_quality",
        data_type="hourly",
        api_key="mugwort_pollen",
    ),
    AthleticLayerSensorDescription(
        key="pollen_olive",
        translation_key="pollen_olive",
        native_unit_of_measurement="grains/m³",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:tree",
        source="air_quality",
        data_type="hourly",
        api_key="olive_pollen",
    ),
    AthleticLayerSensorDescription(
        key="pollen_ragweed",
        translation_key="pollen_ragweed",
        native_unit_of_measurement="grains/m³",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flower-pollen",
        source="air_quality",
        data_type="hourly",
        api_key="ragweed_pollen",
    ),
    # ── Sunrise / Sunset (daily from weather endpoint) ───────────
    AthleticLayerSensorDescription(
        key="sunrise",
        translation_key="sunrise",
        icon="mdi:weather-sunset-up",
        source="weather",
        data_type="daily",
        api_key="sunrise",
    ),
    AthleticLayerSensorDescription(
        key="sunset",
        translation_key="sunset",
        icon="mdi:weather-sunset-down",
        source="weather",
        data_type="daily",
        api_key="sunset",
    ),
)


# ── Platform setup ──────────────────────────────────────────────────


def _build_hourly_rain_descriptions() -> list[AthleticLayerSensorDescription]:
    """Generate 8 sensor descriptions for rain h+1 … h+8."""
    descs: list[AthleticLayerSensorDescription] = []
    for offset in range(1, 9):
        descs.append(
            AthleticLayerSensorDescription(
                key=f"rain_h{offset}",
                translation_key=f"rain_h{offset}",
                native_unit_of_measurement="mm",
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=1,
                icon="mdi:weather-rainy",
                source="rainfall_forecast",
                data_type="rain_hour",
                api_key="",
                hour_offset=offset,
            )
        )
    return descs


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AthleticLayer sensor entities."""
    coordinator: AthleticLayerCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[AthleticLayerSensor] = [
        AthleticLayerSensor(coordinator, desc) for desc in SENSOR_DESCRIPTIONS
    ]
    entities.extend(
        AthleticLayerSensor(coordinator, desc)
        for desc in _build_hourly_rain_descriptions()
    )

    # Advice sensor
    entities.append(AthleticLayerAdviceSensor(coordinator, entry))  # type: ignore[arg-type]

    async_add_entities(entities)


# ── Entity class ────────────────────────────────────────────────────


class AthleticLayerSensor(CoordinatorEntity[AthleticLayerCoordinator], SensorEntity):
    """Representation of a single AthleticLayer sensor."""

    entity_description: AthleticLayerSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AthleticLayerCoordinator,
        description: AthleticLayerSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    # ── stable entity ID ────────────────────────────────────────

    @property
    def suggested_object_id(self) -> str | None:
        """Force English-based entity IDs regardless of system language."""
        return f"athletic_layer {self.entity_description.key}"

    # ── device info ─────────────────────────────────────────────

    @property
    def device_info(self) -> DeviceInfo:
        """Group all sensors under a single device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="Athletic Layer",
            manufacturer="Open-Meteo",
            model="Weather & Air Quality",
            entry_type=DeviceEntryType.SERVICE,
        )

    # ── state value ─────────────────────────────────────────────

    @property
    def native_value(self) -> Any | None:
        """Extract the sensor value from the coordinator data."""
        data = self.coordinator.data
        if data is None:
            return None

        desc = self.entity_description

        # Rainfall forecast is a pre-processed dict at the top level
        if desc.data_type == "direct":
            return data.get(desc.source, {}).get(desc.api_key)

        # Per-hour rain sensor (h+1 … h+8)
        if desc.data_type == "rain_hour":
            hourly = data.get("rainfall_forecast", {}).get("hourly", [])
            idx = desc.hour_offset - 1  # offset 1 → index 0
            if idx < len(hourly):
                return hourly[idx].get("rain_mm")
            return None

        source_data = data.get(desc.source) or {}

        # Daily values (sunrise, sunset) — today is index 0
        if desc.data_type == "daily":
            daily = source_data.get("daily", {})
            values = daily.get(desc.api_key, [])
            if values:
                raw = values[0]  # e.g. "2026-03-02T07:15"
                # Return just the time portion for readability
                if isinstance(raw, str) and "T" in raw:
                    return raw.split("T", 1)[1]
                return raw
            return None

        if desc.data_type == "current":
            value = source_data.get("current", {}).get(desc.api_key)
        elif desc.data_type == "hourly":
            hourly = source_data.get("hourly", {})
            values = hourly.get(desc.api_key, [])
            idx_key = (
                "weather_hour_index"
                if desc.source == "weather"
                else "air_quality_hour_index"
            )
            idx = data.get(idx_key, 0)
            value = values[idx] if idx < len(values) else None
        else:
            value = None

        # Translate WMO weather code → translation key
        if desc.key == "weather_condition" and value is not None:
            return WMO_CODES.get(int(value), f"unknown_{value}")

        # Wind direction → 16-point compass label (degrees in extra attributes)
        if desc.key == "wind_direction" and value is not None:
            return degrees_to_compass(value)

        return value

    # ── extra attributes ────────────────────────────────────────

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Provide extra attributes for specific sensors."""
        data = self.coordinator.data
        if data is None:
            return None

        key = self.entity_description.key

        # 8 h rainfall total: per-hour breakdown
        if key == "rainfall_forecast_8h":
            forecast = data.get("rainfall_forecast", {})
            return {"hourly_forecast": forecast.get("hourly", [])}

        # Per-hour rain sensors: expose time and probability as attributes
        if key.startswith("rain_h"):
            desc = self.entity_description
            hourly = data.get("rainfall_forecast", {}).get("hourly", [])
            idx = desc.hour_offset - 1
            if idx < len(hourly):
                entry = hourly[idx]
                return {
                    "time": entry.get("time"),
                    "precipitation_probability": entry.get("precipitation_probability"),
                }
            return None

        # Wind direction: expose raw degrees alongside the compass label
        if key == "wind_direction":
            source_data = data.get("weather") or {}
            degrees = source_data.get("current", {}).get("wind_direction_10m")
            return {"degrees": degrees}

        return None


# ── Helper ──────────────────────────────────────────────────────────


def _read_user_language(storage_dir: str, user_id: str | None = None) -> str | None:
    """Read a user's language from HA frontend storage files."""
    import os

    try:
        # If a user_id is known, try that specific file first.
        if user_id:
            target = f"frontend.user_data_{user_id}"
            path = os.path.join(storage_dir, target)
            lang = _extract_language_from_file(path)
            if lang:
                return lang

        # Fall back to scanning all user files.
        for name in sorted(os.listdir(storage_dir)):
            if not name.startswith("frontend.user_data_"):
                continue
            path = os.path.join(storage_dir, name)
            lang = _extract_language_from_file(path)
            if lang:
                return lang
    except Exception:
        pass
    return None


def _extract_language_from_file(path: str) -> str | None:
    """Extract the language string from a single frontend storage file."""
    import os

    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        data = raw.get("data") if isinstance(raw, dict) else None
        if not isinstance(data, dict):
            return None
        lang = data.get("language")
        if isinstance(lang, dict):
            lang = lang.get("language")
        if isinstance(lang, str) and lang:
            return lang
    except Exception:
        pass
    return None


def _safe_idx(data: dict, key: str, index: int) -> float | None:
    """Safely get a value from a list inside a dict."""
    lst = data.get(key)
    if lst and isinstance(lst, list) and index < len(lst):
        return lst[index]
    return None


def _build_weather_slice_current(data: dict[str, Any]) -> WeatherSlice:
    """Build a WeatherSlice from the coordinator's current-hour data."""
    weather = data.get("weather", {})
    air = data.get("air_quality") or {}

    current_w = weather.get("current", {})
    hourly_w = weather.get("hourly", {})
    current_a = air.get("current", {}) if air else {}
    hourly_a = air.get("hourly", {}) if air else {}
    idx = data.get("weather_hour_index", 0)
    aq_idx = data.get("air_quality_hour_index", 0)

    # Extract today's sunrise / sunset from the daily arrays
    daily_w = weather.get("daily", {})
    sunrise_list = daily_w.get("sunrise", [])
    sunset_list = daily_w.get("sunset", [])
    sunrise_str = sunrise_list[0] if sunrise_list else None
    sunset_str = sunset_list[0] if sunset_list else None

    return WeatherSlice(
        temperature=current_w.get("temperature_2m"),
        feels_like=current_w.get("apparent_temperature"),
        humidity=current_w.get("relative_humidity_2m"),
        wind_speed=current_w.get("wind_speed_10m"),
        wind_gusts=current_w.get("wind_gusts_10m"),
        precipitation_mm=current_w.get("precipitation"),
        precipitation_probability=_safe_idx(hourly_w, "precipitation_probability", idx),
        uv_index=_safe_idx(hourly_w, "uv_index", idx),
        cloud_cover=current_w.get("cloud_cover"),
        weather_code=current_w.get("weather_code"),
        dew_point=_safe_idx(hourly_w, "dew_point_2m", idx),
        pressure=current_w.get("pressure_msl"),
        aqi=current_a.get("european_aqi") if current_a else None,
        pm25=current_a.get("pm2_5") if current_a else None,
        pollen_grass=_safe_idx(hourly_a, "grass_pollen", aq_idx),
        pollen_birch=_safe_idx(hourly_a, "birch_pollen", aq_idx),
        pollen_ragweed=_safe_idx(hourly_a, "ragweed_pollen", aq_idx),
        sunrise=sunrise_str,
        sunset=sunset_str,
    )


def _build_weather_slice_hourly(data: dict[str, Any], hour_index: int) -> WeatherSlice:
    """Build a WeatherSlice for a specific hourly index."""
    weather = data.get("weather", {})
    air = data.get("air_quality") or {}
    hourly_w = weather.get("hourly", {})
    hourly_a = air.get("hourly", {}) if air else {}

    # Determine which day this hour belongs to and pick matching sunrise/sunset
    daily_w = weather.get("daily", {})
    sunrise_list = daily_w.get("sunrise", [])
    sunset_list = daily_w.get("sunset", [])
    times = hourly_w.get("time", [])
    sunrise_str: str | None = sunrise_list[0] if sunrise_list else None
    sunset_str: str | None = sunset_list[0] if sunset_list else None
    if hour_index < len(times) and sunrise_list:
        hour_date = times[hour_index][:10]  # "YYYY-MM-DD"
        daily_dates = daily_w.get("time", [])
        for d_idx, d_date in enumerate(daily_dates):
            if d_date == hour_date:
                sunrise_str = sunrise_list[d_idx] if d_idx < len(sunrise_list) else None
                sunset_str = sunset_list[d_idx] if d_idx < len(sunset_list) else None
                break

    return WeatherSlice(
        temperature=_safe_idx(hourly_w, "temperature_2m", hour_index),
        feels_like=_safe_idx(hourly_w, "apparent_temperature", hour_index),
        humidity=_safe_idx(hourly_w, "relative_humidity_2m", hour_index),
        wind_speed=_safe_idx(hourly_w, "wind_speed_10m", hour_index),
        wind_gusts=_safe_idx(hourly_w, "wind_gusts_10m", hour_index),
        precipitation_mm=_safe_idx(hourly_w, "precipitation", hour_index),
        precipitation_probability=_safe_idx(
            hourly_w, "precipitation_probability", hour_index
        ),
        uv_index=_safe_idx(hourly_w, "uv_index", hour_index),
        cloud_cover=_safe_idx(hourly_w, "cloud_cover", hour_index),
        weather_code=_safe_idx(hourly_w, "weather_code", hour_index),
        dew_point=_safe_idx(hourly_w, "dew_point_2m", hour_index),
        pressure=_safe_idx(hourly_w, "pressure_msl", hour_index),
        aqi=_safe_idx(hourly_a, "european_aqi", hour_index),
        pm25=_safe_idx(hourly_a, "pm2_5", hour_index),
        pollen_grass=_safe_idx(hourly_a, "grass_pollen", hour_index),
        pollen_birch=_safe_idx(hourly_a, "birch_pollen", hour_index),
        pollen_ragweed=_safe_idx(hourly_a, "ragweed_pollen", hour_index),
        sunrise=sunrise_str,
        sunset=sunset_str,
    )


# ── Advice sensor ───────────────────────────────────────────────────


class AthleticLayerAdviceSensor(
    CoordinatorEntity[AthleticLayerCoordinator], SensorEntity
):
    """Sensor that provides full clothing advice.

    state  = short summary (≤255 chars)
    extra_state_attributes:
        detailed_advice   – full natural-language paragraph
        layers            – dict with base / mid / outer / accessories
        warnings          – list of warning strings
        health_adjustments – list of health-related notes
        advice_hourly     – list of 9 dicts (now + h1…h8)
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:tshirt-crew"

    _LANGUAGE_CHECK_INTERVAL = timedelta(seconds=30)

    def __init__(
        self,
        coordinator: AthleticLayerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the advice sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_clothing_advice"
        self._sport = entry.data.get(CONF_SPORT, "running")
        self._cached_language: str | None = None
        self._attr_name = self._build_display_name(DEFAULT_LANGUAGE)

    @property
    def suggested_object_id(self) -> str | None:
        """Force English-based entity ID regardless of system language."""
        return "athletic_layer clothing_advice"

    async def async_added_to_hass(self) -> None:
        """Register listeners for language changes."""
        await super().async_added_to_hass()

        # Seed the cached language
        self._cached_language = await self.hass.async_add_executor_job(
            self._resolve_language
        )
        self._attr_name = self._build_display_name(self._cached_language)

        # React immediately to system-level language changes
        self.async_on_remove(
            self.hass.bus.async_listen(
                EVENT_CORE_CONFIG_UPDATE, self._async_on_core_config_update
            )
        )

        # React immediately when the Lovelace card reports a language change
        self.async_on_remove(
            self.hass.bus.async_listen(
                "athletic_layer_language_changed",
                self._async_on_frontend_language_changed,
            )
        )

        # Poll for user-profile language changes (stored on disk)
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_check_language,
                self._LANGUAGE_CHECK_INTERVAL,
            )
        )

    @callback
    def _async_on_core_config_update(self, event: Event) -> None:
        """Handle system-level config changes (e.g. language)."""
        self.hass.async_create_task(self._async_check_language())

    @callback
    def _async_on_frontend_language_changed(self, event: Event) -> None:
        """Handle language change reported by the Lovelace card."""
        lang = (event.data.get("language") or "")[:2].lower()
        if lang not in SUPPORTED_LANGUAGES:
            return
        # Persist within this HA session so _resolve_language picks it up.
        self.hass.data.setdefault(DOMAIN, {})["frontend_language"] = lang
        if lang != self._cached_language:
            _LOGGER.debug(
                "Frontend language event: %s -> %s", self._cached_language, lang
            )
            self._cached_language = lang
            self._attr_name = self._build_display_name(lang)
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Handle update_entity calls: re-check language, then refresh data."""
        await self._async_check_language()
        await super().async_update()

    async def _async_check_language(self, _now: datetime | None = None) -> None:
        """Check if the resolved language changed and refresh advice."""
        new_lang = await self.hass.async_add_executor_job(self._resolve_language)
        if new_lang != self._cached_language:
            _LOGGER.debug(
                "AthleticLayer advice language changed: %s -> %s",
                self._cached_language,
                new_lang,
            )
            self._cached_language = new_lang
            self._attr_name = self._build_display_name(new_lang)
            self.async_write_ha_state()

    def _build_display_name(self, lang: str) -> str:
        """Build the translated display name including the sport."""
        label = ADVICE_LABEL.get(lang, ADVICE_LABEL["en"])
        sport = SPORT_NAMES.get(lang, SPORT_NAMES["en"]).get(
            self._sport, self._sport.replace("_", " ").title()
        )
        return f"{label} ({sport})"

    @property
    def device_info(self) -> DeviceInfo:
        """Group under the same device as all other sensors."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="Athletic Layer",
            manufacturer="Open-Meteo",
            model="Weather & Air Quality",
            entry_type=DeviceEntryType.SERVICE,
        )

    # ── state ───────────────────────────────────────────────────

    @property
    def native_value(self) -> str | None:
        """Short summary (≤255 chars)."""
        advice = self._current_advice()
        return advice.summary if advice else None

    # ── attributes ──────────────────────────────────────────────

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Full advice, layers, warnings, and hourly breakdown."""
        data = self.coordinator.data
        if not data:
            return None

        current = self._current_advice()
        if not current:
            return None

        engine = self._build_engine()
        hourly_advice = self._build_hourly_advice(data, engine)

        return {
            "detailed_advice": current.detailed_advice,
            "location": current.location,
            "generated_at": current.generated_at,
            "layers": current.layers,
            "warnings": current.warnings,
            "health_adjustments": current.health_adjustments,
            "advice_hourly": hourly_advice,
            "language": self._cached_language or DEFAULT_LANGUAGE,
            "sport": self._sport,
        }

    # ── private helpers ─────────────────────────────────────────

    def _build_engine(self) -> AdviceEngine:
        sport = self._entry.data.get(CONF_SPORT, "running")
        conditions = self._entry.data.get(CONF_HEALTH_CONDITIONS, [])
        language = self._cached_language or DEFAULT_LANGUAGE
        _LOGGER.debug("AthleticLayer advice engine language: %s", language)
        return AdviceEngine(
            sport=sport,
            health_conditions=conditions,
            language=language,
        )

    def _resolve_language(self) -> str:
        """Resolve advice language from the best available source."""
        # 1) Language reported by the Lovelace card (most accurate)
        fe_lang = self.hass.data.get(DOMAIN, {}).get("frontend_language")
        if fe_lang and fe_lang in SUPPORTED_LANGUAGES:
            return fe_lang

        # 2) User-profile language from storage file
        try:
            storage_dir = self.hass.config.path(".storage")
            user_id = self._entry.data.get(CONF_USER_ID)
            lang = _read_user_language(storage_dir, user_id)
            if lang:
                code = lang[:2].lower()
                if code in SUPPORTED_LANGUAGES:
                    return code
        except Exception:
            pass

        # 3) Fall back to HA system language
        sys_lang = self.hass.config.language
        if sys_lang:
            code = sys_lang[:2].lower()
            if code in SUPPORTED_LANGUAGES:
                return code

        return DEFAULT_LANGUAGE

    def _current_advice(self) -> HourAdvice | None:
        data = self.coordinator.data
        if not data:
            return None
        ws = _build_weather_slice_current(data)
        return self._build_engine().generate(
            ws,
            location=self.coordinator.location_name,
            timezone=self.coordinator.timezone,
        )

    def _build_hourly_advice(
        self, data: dict[str, Any], engine: AdviceEngine
    ) -> list[dict[str, Any]]:
        """Build advice for current hour + 8 hours ahead."""
        weather = data.get("weather", {})
        hourly_w = weather.get("hourly", {})
        times = hourly_w.get("time", [])
        base_idx = data.get("weather_hour_index", 0)

        result: list[dict[str, Any]] = []
        for offset in range(9):  # now + h1…h8
            i = base_idx + offset
            if i >= len(times):
                break
            ws = _build_weather_slice_hourly(data, i)
            ha = engine.generate(
                ws,
                location=self.coordinator.location_name,
                timezone=self.coordinator.timezone,
            )
            ha.time = times[i]
            result.append(
                {
                    "time": ha.time,
                    "summary": ha.summary,
                    "detailed_advice": ha.detailed_advice,
                    "layers": ha.layers,
                    "warnings": ha.warnings,
                }
            )
        return result
