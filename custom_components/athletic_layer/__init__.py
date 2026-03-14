"""The AthleticLayer integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import AthleticLayerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# All sensor description keys that must map to English entity IDs.
_SENSOR_KEYS = [
    "temperature", "feels_like_temperature", "weather_condition",
    "wind_speed", "wind_direction", "wind_gusts", "humidity",
    "pressure", "cloud_cover", "precipitation", "uv_index",
    "dew_point", "precipitation_probability", "rainfall_forecast_8h",
    "air_quality_index", "pm25", "pm10",
    "pollen_grass", "pollen_birch", "pollen_alder",
    "pollen_mugwort", "pollen_olive", "pollen_ragweed",
    "sunrise", "sunset", "clothing_advice",
    *[f"rain_h{i}" for i in range(1, 9)],
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AthleticLayer from a config entry."""
    coordinator = AthleticLayerCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Migrate translated entity IDs (e.g. Dutch) to stable English names.
    _migrate_entity_ids(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload when the user changes options via the UI
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def _migrate_entity_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Rename translated entity IDs to stable English-based names.

    On non-English HA systems, entity IDs were derived from the translated
    sensor name (e.g. ``temperatuur`` instead of ``temperature``).  This
    one-time migration renames them so the Lovelace card can find them.
    """
    ent_reg = er.async_get(hass)

    for key in _SENSOR_KEYS:
        unique_id = f"{entry.entry_id}_{key}"
        current_entity_id = ent_reg.async_get_entity_id(
            "sensor", DOMAIN, unique_id
        )
        if current_entity_id is None:
            continue

        expected_entity_id = f"sensor.athletic_layer_{key}"
        if current_entity_id == expected_entity_id:
            continue

        # Only rename when the target is not already occupied.
        if ent_reg.async_get(expected_entity_id) is not None:
            _LOGGER.debug(
                "Cannot migrate %s → %s (target already exists)",
                current_entity_id,
                expected_entity_id,
            )
            continue

        _LOGGER.info(
            "Migrating entity ID: %s → %s", current_entity_id, expected_entity_id
        )
        ent_reg.async_update_entity(
            current_entity_id, new_entity_id=expected_entity_id
        )
