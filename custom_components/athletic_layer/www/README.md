# Athletic Layer Card

A custom Lovelace card for the **Athletic Layer** integration, displaying real-time weather conditions and personalized clothing advice for athletes.

## Features

- **Weather header** – current temperature, feels-like, condition icon
- **Weather details grid** – wind, humidity, UV, precipitation, clouds, sunrise/sunset
- **Clothing advice** – detailed text with layer-by-layer breakdown
- **Warnings & alerts** – extreme-weather and health-condition alerts
- **8-hour rain forecast** – bar chart with mm and probability per hour
- **Air quality** – European AQI badge, PM2.5/PM10 values
- **Pollen levels** – grass, birch, alder, mugwort, olive, ragweed
- **Hourly advice carousel** – scrollable cards for the next 8 hours

## Installation

1. **Copy the card file** to your Home Assistant `www` folder:

   ```
   <config>/www/athletic-layer-card.js
   ```

   The file is located at `custom_components/AthleticLayer/www/athletic-layer-card.js`.  
   Copy (or symlink) it into `<config>/www/`:

   ```bash
   cp custom_components/AthleticLayer/www/athletic-layer-card.js www/
   ```

2. **Register the resource** in Home Assistant:

   Go to **Settings → Dashboards → Resources** (top-right menu) → **Add Resource**:

   | Field | Value |
   |-------|-------|
   | URL   | `/local/athletic-layer-card.js?v=1.0.x` |
   | Type  | JavaScript Module |

3. **Prevent caching** by adding `?v=1.0.x` where x is preferably the same version as indicated
    in the source on line 16 `const CARD_VERSION = "1.0.3";` you are preventing the browser from caching the previous version of the card.

5. **Add the card** to a dashboard.

## Usage

### Minimal YAML

Just set the `zone` to the name of the HA zone you configured in the integration:

```yaml
type: custom:athletic-layer-card
zone: home
```

This automatically finds all sensors for that zone (e.g. `sensor.home_temperature`,
`sensor.home_clothing_advice`, etc.).

### Full configuration

```yaml
type: custom:athletic-layer-card
zone: home                     # Zone slug matching your HA zone (e.g. "home", "work")
name: Athletic Layer           # Card title (default: "Athletic Layer")
show_weather_details: true     # Weather grid with wind, UV, etc. (default: true)
show_rain_chart: true          # 8-hour rain bar chart (default: true)
show_air_quality: true         # AQI, PM2.5, PM10 section (default: true)
show_pollen: true              # Pollen chips inside AQ section (default: true)
show_hourly_advice: true       # Scrollable hourly advice cards (default: true)
```

### Multiple zones

Add one card per zone:

```yaml
type: custom:athletic-layer-card
zone: home
```

```yaml
type: custom:athletic-layer-card
zone: work
```

### Advanced: explicit entity

Instead of `zone`, you can point directly to the clothing advice entity. The card
derives the prefix from the entity name automatically:

```yaml
type: custom:athletic-layer-card
entity: sensor.home_clothing_advice
```

You can also override the prefix manually if needed:

```yaml
type: custom:athletic-layer-card
entity: sensor.home_clothing_advice
entity_prefix: sensor.home_
```

## Card sections

| Section | Toggle option | Description |
|---------|--------------|-------------|
| Header | always shown | Temperature, feels-like, condition icon, location |
| Weather grid | `show_weather_details` | 3×3 grid of wind, humidity, UV, rain, clouds, sunrise/sunset |
| Clothing advice | always shown | Detailed natural-language advice + layer breakdown |
| Alerts | always shown (when data present) | Warnings and health adjustments |
| Rain forecast | `show_rain_chart` | 8-hour bar chart with mm and probability |
| Air quality | `show_air_quality` | European AQI badge + PM values |
| Pollen | `show_pollen` | Pollen chips (only shown if levels > 0) |
| Hourly advice | `show_hourly_advice` | Horizontally scrollable cards for hours +1 to +8 |

## Theming

The card uses standard Home Assistant CSS variables and adapts to both light and dark themes automatically.
