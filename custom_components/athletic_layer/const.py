"""Constants for the AthleticLayer integration."""

from __future__ import annotations

DOMAIN = "AthleticLayer"

# ── Configuration keys ──────────────────────────────────────────────
CONF_SPORT = "sport"
CONF_HEALTH_CONDITIONS = "health_conditions"
CONF_USER_ID = "user_id"
CONF_ZONE = "zone"

SPORT_RUNNING = "running"
SPORT_CYCLING = "cycling"
SPORT_HIKING = "hiking"
SPORT_WALKING = "walking"
SPORTS = [SPORT_RUNNING, SPORT_CYCLING, SPORT_HIKING, SPORT_WALKING]

SUPPORTED_LANGUAGES = {"en", "nl", "de", "fr", "es"}
DEFAULT_LANGUAGE = "en"

# ── Translated sport display names per language ─────────────────────
SPORT_NAMES: dict[str, dict[str, str]] = {
    "en": {"running": "Running", "cycling": "Cycling", "hiking": "Hiking", "walking": "Walking"},
    "nl": {"running": "Hardlopen", "cycling": "Fietsen", "hiking": "Wandelen", "walking": "Wandelen"},
    "de": {"running": "Laufen", "cycling": "Radfahren", "hiking": "Wandern", "walking": "Gehen"},
    "fr": {"running": "Course", "cycling": "Cyclisme", "hiking": "Randonnée", "walking": "Marche"},
    "es": {"running": "Correr", "cycling": "Ciclismo", "hiking": "Senderismo", "walking": "Caminar"},
}

ADVICE_LABEL: dict[str, str] = {
    "en": "Clothing Advice",
    "nl": "Kledingadvies",
    "de": "Kleidungsempfehlung",
    "fr": "Conseil vestimentaire",
    "es": "Consejo de vestimenta",
}

# ── Unit systems per language ───────────────────────────────────────
# English (US) → imperial; all others → metric.
# Keys: temp_unit, speed_unit, rain_unit, pressure_unit
UNIT_PROFILES: dict[str, dict[str, str]] = {
    "en": {"temp_unit": "°F", "speed_unit": "mph", "rain_unit": "in", "pressure_unit": "inHg"},
    "nl": {"temp_unit": "°C", "speed_unit": "km/u", "rain_unit": "mm", "pressure_unit": "hPa"},
    "de": {"temp_unit": "°C", "speed_unit": "km/h", "rain_unit": "mm", "pressure_unit": "hPa"},
    "fr": {"temp_unit": "°C", "speed_unit": "km/h", "rain_unit": "mm", "pressure_unit": "hPa"},
    "es": {"temp_unit": "°C", "speed_unit": "km/h", "rain_unit": "mm", "pressure_unit": "hPa"},
}
DEFAULT_UNIT_PROFILE: dict[str, str] = UNIT_PROFILES["en"]

HEALTH_CONDITIONS: list[str] = [
    "asthma",
    "pollen_allergy",
    "cold_sensitivity",
    "heat_sensitivity",
    "rheumatism",
    "hyperhidrosis",
    "sun_sensitivity",
    "cardiovascular",
    "diabetes",
    "immunosuppression",
]

# ── API URLs ────────────────────────────────────────────────────────
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# ── Polling / forecast window ───────────────────────────────────────
UPDATE_INTERVAL_MINUTES = 10
FORECAST_HOURS = 48  # enough to cover current hour + 8 h ahead from any time of day

# ── WMO Weather interpretation codes ───────────────────────────────
WMO_CODES: dict[int, str] = {
    0: "clear_sky",
    1: "mainly_clear",
    2: "partly_cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing_rime_fog",
    51: "light_drizzle",
    53: "moderate_drizzle",
    55: "dense_drizzle",
    56: "light_freezing_drizzle",
    57: "dense_freezing_drizzle",
    61: "slight_rain",
    63: "moderate_rain",
    65: "heavy_rain",
    66: "light_freezing_rain",
    67: "heavy_freezing_rain",
    71: "slight_snow_fall",
    73: "moderate_snow_fall",
    75: "heavy_snow_fall",
    77: "snow_grains",
    80: "slight_rain_showers",
    81: "moderate_rain_showers",
    82: "violent_rain_showers",
    85: "slight_snow_showers",
    86: "heavy_snow_showers",
    95: "thunderstorm",
    96: "thunderstorm_slight_hail",
    99: "thunderstorm_heavy_hail",
}
