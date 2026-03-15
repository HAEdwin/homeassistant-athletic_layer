# Athletic Layer

[![version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange)]()

A **Home Assistant** custom integration that provides personalized clothing advice for outdoor **runners**, **walkers/hikers** and **cyclists**. It fetches real-time weather, air quality, and pollen data from the [Open-Meteo](https://open-meteo.com/) API and generates sport-specific layering recommendations adapted to your health conditions. Includes a custom Lovelace card with live weather, an 8-hour rain forecast, and hourly outfit tips — in 5 languages.

---

## Features

- **Personalized clothing advice** — layered recommendations (base, mid, outer, bottoms, accessories) based on current and forecasted weather.
- **Sport-specific intelligence** — separate advice profiles for running (higher body heat), cycling (higher wind exposure), Walking and Hiking.
- **Health-aware adjustments** — adapts to conditions like asthma, pollen allergy, cold/heat sensitivity, rheumatism, hyperhidrosis, sun sensitivity, cardiovascular issues, diabetes, and immunosuppression.
- **30+ weather sensors** — temperature, feels-like, wind, humidity, UV, precipitation, cloud cover, sunrise/sunset, and more.
- **Air quality & pollen** — European AQI, PM2.5, PM10, and 6 pollen types (grass, birch, alder, mugwort, olive, ragweed).
- **8-hour rain forecast** — with per-hour mm and precipitation probability.
- **Hourly advice** — clothing recommendations for each of the next 8 hours.
- **Multi-language** — English, Dutch, German, French, and Spanish.
- **Custom Lovelace card** — a polished card displaying all data at a glance.

---

## Installation

### HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Go to **Integrations** → **⋮** (top-right menu) → **Custom repositories**.
3. Add the repository URL and select **Integration** as the category.
4. Search for **Athletic Layer** and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `AthleticLayer` folder into your Home Assistant `custom_components` directory:

   ```
   <config>/custom_components/athletic_layer
   ```

2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Athletic Layer**.
3. Fill in the setup form:

   | Field | Description |
   |-------|-------------|
   | **Zone** | A Home Assistant zone entity (e.g. `zone.home`) — used for location coordinates. |
   | **Sport** | `Running` or `Cycling` — adjusts advice for body heat and wind exposure. |
   | **Health conditions** | Optional — select any that apply to receive tailored warnings and adjustments. |

4. The integration will immediately start polling weather and air quality data (every 10 minutes).

You can reconfigure sport and health settings at any time via **Settings → Devices & Services → Athletic Layer → Configure**.

---

## Sensors created

The integration creates a device with the following sensors:

| Sensor | Description |
|--------|-------------|
| **Clothing Advice** | Main advice text with attributes: `detailed_advice`, `layers`, `warnings`, `health_adjustments`, `advice_hourly` |
| **Temperature** | Current temperature (°C) |
| **Feels Like Temperature** | Apparent temperature (°C) |
| **Weather Condition** | Current condition (clear sky, rain, snow, etc.) |
| **Wind Speed / Gusts / Direction** | Wind data |
| **Humidity** | Relative humidity (%) |
| **UV Index** | Current UV index |
| **Precipitation / Probability** | Current rain and chance of rain |
| **Cloud Cover** | Cloud cover (%) |
| **Sunrise / Sunset** | Today's sunrise and sunset times |
| **Rainfall Forecast 8h** | Total forecasted rain with hourly breakdown |
| **Air Quality Index** | European AQI |
| **PM2.5 / PM10** | Particulate matter concentrations |
| **Pollen** | Grass, birch, alder, mugwort, olive, ragweed levels |

---

## Lovelace Card

A custom card is included to display all integration data in a single dashboard card.

### Card installation

1. Copy the card file to your `www` folder:

   ```bash
   cp custom_components/Athletic_Layer/www/athletic-layer-card.js www/
   ```

2. In Home Assistant, go to **Settings → Dashboards → Resources** → **Add Resource**:

   | Field | Value |
   |-------|-------|
   | URL   | `/local/athletic-layer-card.js` |
   | Type  | JavaScript Module |

3. Add the card to a dashboard.

### Minimal card YAML

```yaml
type: custom:athletic-layer-card
entity: sensor.athletic_layer_zone_zone_clothing_advice
```

### Full card configuration

```yaml
type: custom:athletic-layer-card
entity: sensor.athletic_layer_zone_zone_clothing_advice
name: Athletic Layer           # Card title (default: "Athletic Layer")
show_weather_details: true     # Weather grid (default: true)
show_rain_chart: true          # 8-hour rain bar chart (default: true)
show_air_quality: true         # AQI + PM section (default: true)
show_pollen: true              # Pollen chips (default: true)
show_hourly_advice: true       # Hourly advice carousel (default: true)
```

### Multiple zones

If you have more than one Athletic Layer config entry, set the entity prefix explicitly.
sensor entities will be shown automatically when typing. for example:

```yaml
type: custom:athletic-layer-card
entity: sensor.athletic_layer_zone2_zone2_clothing_advice
```

---

## Supported health conditions

| Condition | Effect on advice |
|-----------|-----------------|
| **Asthma** | Warns about cold/dry air and high particulate matter; suggests face coverings |
| **Pollen allergy** | Suggests tighter-woven fabrics and long sleeves during high pollen counts |
| **Cold sensitivity** | Recommends additional insulation earlier than standard |
| **Heat sensitivity** | Suggests moisture-wicking and ventilated clothing sooner |
| **Rheumatism** | Emphasizes joint warmth and thermal layers in damp/low-pressure conditions |
| **Hyperhidrosis** | Suggests highly breathable, moisture-wicking base layers |
| **Sun sensitivity** | Advises UV-protective clothing and hats during high UV |
| **Cardiovascular** | Extra caution for extreme temperatures and humidity |
| **Diabetes** | Extra foot protection and moisture management |
| **Immunosuppression** | Additional skin coverage during high pollen/pollution |

---

## Supported languages

| Language | Code |
|----------|------|
| English  | `en` |
| Dutch    | `nl` |
| German   | `de` |
| French   | `fr` |
| Spanish  | `es` |

The integration and card automatically use the language configured in your Home Assistant user profile.

---

## Data sources

All weather and environmental data is sourced from the free [Open-Meteo API](https://open-meteo.com/) — no API key required.

---

## License

This project is provided as-is for personal, non-commercial use.
