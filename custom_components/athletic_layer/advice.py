"""Advice engine — generates personalized clothing recommendations.

This module is pure Python with no Home Assistant dependency so it can be
unit-tested independently.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from .advice_templates import get_templates
from .const import DEFAULT_UNIT_PROFILE, UNIT_PROFILES

# ── Localised date formatting ───────────────────────────────────────

_EN_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_EN_MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]


def _format_datetime(dt: datetime, templates: dict[str, list[str]]) -> str:
    """Format a datetime with localised day and month names from templates."""
    days = templates.get("day_names", _EN_DAYS)
    months = templates.get("month_names", _EN_MONTHS)
    day_name = days[dt.weekday()]
    month_name = months[dt.month - 1]
    return f"{day_name} {dt.day} {month_name} {dt.year}, {dt.strftime('%H:%M')}"


# ── Unit conversion helpers ─────────────────────────────────────────

def _convert_speed(kmh: float, unit: str) -> float:
    """Convert km/h to the target speed unit."""
    if unit == "mph":
        return kmh * 0.621371
    if unit == "m/s":
        return kmh / 3.6
    return kmh  # km/h or km/u


def _convert_rain(mm: float, unit: str) -> float:
    """Convert mm to the target precipitation unit."""
    if unit == "in":
        return mm * 0.0393701
    if unit == "cm":
        return mm / 10.0
    return mm  # mm


def _convert_pressure(hpa: float, unit: str) -> float:
    """Convert hPa to the target pressure unit."""
    if unit == "inHg":
        return hpa * 0.02953
    return hpa  # hPa or mb


def _convert_temp(celsius: float, unit: str) -> float:
    """Convert °C to the target temperature unit."""
    if unit == "°F":
        return celsius * 9.0 / 5.0 + 32.0
    return celsius  # °C


# ── Data container for a single hour's weather snapshot ─────────────


@dataclass
class WeatherSlice:
    """Weather snapshot for one hour."""

    temperature: float | None = None
    feels_like: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    wind_gusts: float | None = None
    precipitation_mm: float | None = None
    precipitation_probability: float | None = None
    uv_index: float | None = None
    cloud_cover: float | None = None
    weather_code: int | None = None
    dew_point: float | None = None
    pressure: float | None = None
    # Air quality / pollen
    aqi: float | None = None
    pm25: float | None = None
    pollen_grass: float | None = None
    pollen_birch: float | None = None
    pollen_ragweed: float | None = None
    # Sunrise / sunset (ISO-8601 local time strings, e.g. "2026-03-02T07:15")
    sunrise: str | None = None
    sunset: str | None = None


# ── Result container ────────────────────────────────────────────────


@dataclass
class HourAdvice:
    """Advice for a single hour."""

    time: str = ""
    location: str = ""
    generated_at: str = ""
    summary: str = ""
    detailed_advice: str = ""
    layers: dict[str, str | list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    health_adjustments: list[str] = field(default_factory=list)


# ── Template picker ─────────────────────────────────────────────────


def _pick(
    templates: dict[str, list[str]],
    key: str,
    seed: str = "",
    **fmt: object,
) -> str:
    """Pick one template variant for *key*. Deterministic within an hour."""
    pool = templates.get(key, [])
    if not pool:
        return ""
    idx = int(hashlib.md5(f"{key}:{seed}".encode()).hexdigest(), 16) % len(pool)
    text = pool[idx]
    if fmt:
        text = text.format(**fmt)
    return text


# ── Main engine ─────────────────────────────────────────────────────


class AdviceEngine:
    """Generate personalized clothing advice based on weather + health."""

    def __init__(
        self,
        sport: str,
        health_conditions: list[str],
        language: str = "en",
    ) -> None:
        self._sport = sport
        self._conditions = set(health_conditions)
        self._lang = language
        self._t = get_templates(language)
        self._units = UNIT_PROFILES.get(language, DEFAULT_UNIT_PROFILE)

    # ── sunrise / sunset helper ─────────────────────────────────

    @staticmethod
    def _is_daytime(weather: WeatherSlice, now: datetime) -> bool:
        """Return True if *now* is between sunrise and sunset.

        Falls back to True (assume day) if sunrise/sunset data is missing.
        """
        if not weather.sunrise or not weather.sunset:
            return True  # no data → assume day
        try:
            sunrise = datetime.fromisoformat(weather.sunrise)
            sunset = datetime.fromisoformat(weather.sunset)
            # Make naive if tz-aware comparison would fail
            if sunrise.tzinfo is None and now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            elif sunrise.tzinfo is not None and now.tzinfo is None:
                sunrise = sunrise.replace(tzinfo=None)
                sunset = sunset.replace(tzinfo=None)
            return sunrise <= now <= sunset
        except (ValueError, TypeError):
            return True

    # ── public API ──────────────────────────────────────────────

    def generate(
        self,
        weather: WeatherSlice,
        location: str = "",
        generated_at: datetime | None = None,
        timezone: str = "",
    ) -> HourAdvice:
        """Produce advice for a single weather slice."""
        sentences: list[str] = []
        warnings: list[str] = []
        health_adj: list[str] = []
        layers: dict[str, str | list[str]] = {
            "base": _pick(self._t, "layer_mid_none"),
            "mid": _pick(self._t, "layer_mid_none"),
            "outer": _pick(self._t, "layer_outer_none"),
            "bottoms": _pick(self._t, "layer_mid_none"),
            "accessories": [],
        }

        # ── Location & timestamp preamble ───────────────────────
        if generated_at:
            now = generated_at
        elif timezone:
            try:
                now = datetime.now(tz=ZoneInfo(timezone))
            except (KeyError, Exception):
                now = datetime.now()
        else:
            now = datetime.now()
        timestamp_str = _format_datetime(now, self._t)
        seed = now.strftime("%Y%m%d%H")  # stable within the same hour

        if location:
            sentences.append(
                _pick(
                    self._t,
                    "preamble_location",
                    seed,
                    location=location,
                    timestamp=timestamp_str,
                )
            )
        else:
            sentences.append(
                _pick(self._t, "preamble_no_location", seed, timestamp=timestamp_str)
            )

        # ── Temperature & base layer ────────────────────────────
        sentences.append(self._temperature_advice(weather, layers, seed))

        # ── Rain ────────────────────────────────────────────────
        sentences.append(self._rain_advice(weather, layers, seed))

        # ── Wind ────────────────────────────────────────────────
        sentences.append(self._wind_advice(weather, layers, seed))

        # ── UV / Cloud combined ─────────────────────────────────
        is_day = self._is_daytime(weather, now)
        sentences.append(self._uv_cloud_advice(weather, layers, seed, is_day))

        # ── Health condition adjustments ─────────────────────────
        h_adj, h_warn = self._health_adjustments(weather, layers, seed, is_day)
        health_adj.extend(h_adj)
        warnings.extend(h_warn)

        # Compose final text
        detailed = " ".join(s for s in sentences if s)
        if health_adj:
            detailed += " " + " ".join(health_adj)
        summary = detailed[:252] + "…" if len(detailed) > 255 else detailed

        return HourAdvice(
            location=location,
            generated_at=timestamp_str,
            summary=summary,
            detailed_advice=detailed,
            layers=layers,
            warnings=warnings,
            health_adjustments=health_adj,
        )

    # ── private helpers ─────────────────────────────────────────

    def _effective_temp(self, weather: WeatherSlice) -> float:
        """Compute an effective 'feels like' temperature with corrections."""
        feels = (
            weather.feels_like
            if weather.feels_like is not None
            else (weather.temperature or 20.0)
        )

        # Health offsets
        if "cold_sensitivity" in self._conditions:
            feels -= 2.0
        if "heat_sensitivity" in self._conditions:
            feels += 2.0

        # Sport correction
        if self._sport == "cycling":
            feels -= 3.0
        elif self._sport == "running":
            feels += 2.0

        return feels

    def _temperature_advice(
        self,
        weather: WeatherSlice,
        layers: dict[str, str | list[str]],
        seed: str,
    ) -> str:
        adjusted = self._effective_temp(weather)
        acc = self._accessories(layers)
        t = self._t
        bike = self._sport == "cycling"

        if adjusted >= 30:
            layers["base"] = _pick(t, "layer_base_singlet")
            layers["bottoms"] = _pick(
                t, "bottom_bike_shorts" if bike else "bottom_run_shorts"
            )
            return _pick(t, "temp_hot", seed)
        if adjusted >= 20:
            layers["base"] = _pick(t, "layer_base_singlet")
            layers["bottoms"] = _pick(
                t, "bottom_bike_shorts" if bike else "bottom_run_shorts"
            )
            return _pick(t, "temp_warm", seed)
        if adjusted >= 15:
            layers["base"] = _pick(t, "layer_base_short")
            layers["bottoms"] = _pick(
                t, "bottom_bike_shorts" if bike else "bottom_run_shorts"
            )
            return _pick(t, "temp_cool", seed)
        if adjusted >= 5:
            layers["base"] = _pick(t, "layer_base_long")
            layers["mid"] = _pick(t, "layer_mid_light")
            layers["bottoms"] = _pick(
                t, "bottom_bike_34_tights" if bike else "bottom_run_34_tights"
            )
            arm_w = _pick(t, "acc_arm_warmers")
            if arm_w not in acc:
                acc.append(arm_w)
            layers["accessories"] = acc
            return _pick(t, "temp_chilly", seed)
        if adjusted >= -5:
            layers["base"] = _pick(t, "layer_base_thermal")
            layers["mid"] = _pick(t, "layer_mid_insulating")
            layers["outer"] = _pick(t, "layer_outer_windproof")
            layers["bottoms"] = _pick(
                t, "bottom_bike_tights" if bike else "bottom_run_tights"
            )
            acc.extend([_pick(t, "acc_gloves"), _pick(t, "acc_headband")])
            leg_w = _pick(t, "acc_leg_warmers")
            if bike and leg_w not in acc:
                acc.append(leg_w)
            layers["accessories"] = acc
            return _pick(t, "temp_cold", seed)
        # Below -5 °C
        layers["base"] = _pick(t, "layer_base_thermal")
        layers["mid"] = _pick(t, "layer_mid_insulating")
        layers["outer"] = _pick(t, "layer_outer_windproof")
        layers["bottoms"] = _pick(
            t, "bottom_bike_thermal_tights" if bike else "bottom_run_thermal_tights"
        )
        acc.extend([_pick(t, "acc_gloves"), _pick(t, "acc_headband")])
        leg_w = _pick(t, "acc_leg_warmers")
        if leg_w not in acc:
            acc.append(leg_w)
        layers["accessories"] = acc
        return _pick(t, "temp_freezing", seed)

    def _rain_advice(
        self,
        weather: WeatherSlice,
        layers: dict[str, str | list[str]],
        seed: str,
    ) -> str:
        prob = weather.precipitation_probability or 0
        mm = weather.precipitation_mm or 0
        t = self._t

        if prob < 20 and mm < 0.1:
            return _pick(t, "rain_none", seed)

        if prob < 50 or mm < 1.0:
            return _pick(t, "rain_slight", seed)

        layers["outer"] = _pick(t, "layer_outer_rain")
        rain_unit = self._units["rain_unit"]
        converted_mm = _convert_rain(mm, rain_unit)
        precision = 2 if rain_unit == "in" else 1
        result = _pick(t, "rain_likely", seed, prob=int(prob), mm=f"{converted_mm:.{precision}f}", rain_unit=rain_unit)
        if self._sport == "cycling":
            acc = self._accessories(layers)
            rain_covers = _pick(t, "acc_rain_shoe_covers")
            if rain_covers not in acc:
                acc.append(rain_covers)
            layers["accessories"] = acc
            result += " " + _pick(t, "rain_cycling_add", seed)
        return result

    def _wind_advice(
        self,
        weather: WeatherSlice,
        layers: dict[str, str | list[str]],
        seed: str,
    ) -> str:
        speed = weather.wind_speed or 0
        gusts = weather.wind_gusts or 0
        t = self._t

        if speed < 15:
            return _pick(t, "wind_calm", seed)

        speed_unit = self._units["speed_unit"]
        c_speed = _convert_speed(speed, speed_unit)
        c_gusts = _convert_speed(gusts, speed_unit)

        if speed < 30:
            if self._sport == "cycling":
                none_label = _pick(t, "layer_outer_none")
                if layers.get("outer") in (none_label, None, "None"):
                    layers["outer"] = _pick(t, "layer_outer_wind_vest")
                return _pick(t, "wind_moderate_bike", seed, speed=f"{c_speed:.0f}", speed_unit=speed_unit)
            return _pick(t, "wind_moderate", seed, speed=f"{c_speed:.0f}", speed_unit=speed_unit)

        # Strong wind
        layers["outer"] = _pick(t, "layer_outer_windproof")
        return _pick(t, "wind_strong", seed, speed=f"{c_speed:.0f}", gusts=f"{c_gusts:.0f}", speed_unit=speed_unit)

    def _uv_cloud_advice(
        self,
        weather: WeatherSlice,
        layers: dict[str, str | list[str]],
        seed: str,
        is_day: bool = True,
    ) -> str:
        """Combined cloud + UV advice as a single natural sentence."""
        acc = self._accessories(layers)
        t = self._t

        # ── Nighttime: skip all sun/UV advice ───────────────────
        if not is_day:
            sentence = _pick(t, "night_no_uv", seed)
            # Recommend reflective gear at night
            refl = _pick(t, "acc_reflective_vest")
            if refl not in acc:
                acc.append(refl)
            layers["accessories"] = acc
            return sentence

        # ── Daytime: original cloud + UV logic ──────────────────
        uv = weather.uv_index or 0
        cloud = weather.cloud_cover or 0

        # Determine cloud band
        if cloud > 70:
            cloud_band = "heavy"
        elif cloud > 40:
            cloud_band = "partial"
        else:
            cloud_band = "clear"

        # Determine UV band
        if uv >= 6:
            uv_band = "high"
        elif uv >= 3:
            uv_band = "mod"
        else:
            uv_band = "low"

        key = f"cloud_{cloud_band}_uv_{uv_band}"
        sentence = _pick(t, key, seed)

        # Accessories based on UV
        if uv_band == "high":
            for acc_key in ("acc_cap", "acc_sunscreen", "acc_sunglasses"):
                item = _pick(t, acc_key)
                if item not in acc:
                    acc.append(item)
        elif uv_band == "mod":
            sunscreen = _pick(t, "acc_sunscreen")
            if sunscreen not in acc:
                acc.append(sunscreen)
            if cloud_band != "heavy":
                sg = _pick(t, "acc_sunglasses")
                if sg not in acc:
                    acc.append(sg)

        # Sun sensitivity extra warning
        if "sun_sensitivity" in self._conditions and uv_band in ("high", "mod"):
            sentence += " " + _pick(t, "sun_sensitivity_warning", seed)
            base = layers.get("base", "")
            if isinstance(base, str):
                # Upgrade short-sleeve to long-sleeve base
                short_label = _pick(t, "layer_base_short")
                if base == short_label:
                    layers["base"] = _pick(t, "layer_base_long")

        layers["accessories"] = acc
        return sentence

    def _health_adjustments(
        self,
        weather: WeatherSlice,
        layers: dict[str, str | list[str]],
        seed: str,
        is_day: bool = True,
    ) -> tuple[list[str], list[str]]:
        """Return (adjustments, warnings) based on health conditions."""
        adjustments: list[str] = []
        warnings: list[str] = []
        acc = self._accessories(layers)
        t = self._t

        feels = (
            weather.feels_like
            if weather.feels_like is not None
            else (weather.temperature or 20)
        )

        has_condition = False

        # Asthma ─────────────────────────────────────────────────
        if "asthma" in self._conditions:
            has_condition = True
            if (weather.pm25 or 0) > 25:
                warnings.append(_pick(t, "asthma_pm_high", seed))
                mask = _pick(t, "acc_face_mask")
                if mask not in acc:
                    acc.append(mask)
            elif feels < 0:
                adjustments.append(_pick(t, "asthma_cold", seed))
                buff = _pick(t, "acc_buff")
                if buff not in acc:
                    acc.append(buff)
            else:
                adjustments.append(_pick(t, "asthma_ok", seed))

        # Pollen allergy ─────────────────────────────────────────
        if "pollen_allergy" in self._conditions:
            has_condition = True
            max_pollen = max(
                weather.pollen_grass or 0,
                weather.pollen_birch or 0,
                weather.pollen_ragweed or 0,
            )
            if max_pollen > 50:
                warnings.append(_pick(t, "pollen_high", seed))
            else:
                adjustments.append(_pick(t, "pollen_ok", seed))

        # Rheumatism ─────────────────────────────────────────────
        if "rheumatism" in self._conditions:
            has_condition = True
            if (weather.pressure or 1013) < 1000 or (weather.humidity or 0) > 80:
                adjustments.append(_pick(t, "rheumatism_bad", seed))
                for acc_key in ("acc_knee_sleeves", "acc_warm_gloves"):
                    item = _pick(t, acc_key)
                    if item not in acc:
                        acc.append(item)
            else:
                adjustments.append(_pick(t, "rheumatism_ok", seed))

        # Hyperhidrosis ──────────────────────────────────────────
        if "hyperhidrosis" in self._conditions:
            has_condition = True
            adjustments.append(_pick(t, "hyperhidrosis", seed))

        # Sun sensitivity (only relevant during daytime) ────────
        if (
            "sun_sensitivity" in self._conditions
            and is_day
            and (weather.uv_index or 0) >= 3
        ):
            has_condition = True
            adjustments.append(_pick(t, "sun_sensitivity_uv", seed))

        # Cardiovascular ─────────────────────────────────────────
        if "cardiovascular" in self._conditions:
            has_condition = True
            if feels > 32 or feels < -5:
                warnings.append(_pick(t, "cardiovascular_extreme", seed))
            else:
                adjustments.append(_pick(t, "cardiovascular_ok", seed))

        # Diabetes ───────────────────────────────────────────────
        if "diabetes" in self._conditions:
            has_condition = True
            adjustments.append(_pick(t, "diabetes_advice", seed))
            socks = _pick(t, "acc_wicking_socks")
            if socks not in acc:
                acc.append(socks)

        # Immunosuppression ──────────────────────────────────────
        if "immunosuppression" in self._conditions:
            has_condition = True
            max_pollen = max(
                weather.pollen_grass or 0,
                weather.pollen_birch or 0,
                weather.pollen_ragweed or 0,
            )
            if (weather.aqi or 0) > 50 or max_pollen > 30:
                warnings.append(_pick(t, "immunosuppression_bad", seed))

        # If user has conditions but everything looks fine
        if has_condition and not adjustments and not warnings:
            adjustments.append(_pick(t, "health_all_clear", seed))

        layers["accessories"] = acc
        return adjustments, warnings

    # ── utility ─────────────────────────────────────────────────

    @staticmethod
    def _accessories(layers: dict[str, str | list[str]]) -> list[str]:
        """Return the accessories list, ensuring it is always a list."""
        acc = layers.get("accessories", [])
        if not isinstance(acc, list):
            acc = []
        return acc
