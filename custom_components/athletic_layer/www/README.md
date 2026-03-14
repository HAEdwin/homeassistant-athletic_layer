# Athletic Layer Card

A custom Lovelace card for the **Athletic Layer** integration, displaying real-time weather conditions and personalized clothing advice for athletes.

![card preview](https://via.placeholder.com/400x600?text=Athletic+Layer+Card)

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
   | URL   | `/local/athletic-layer-card.js` |
   | Type  | JavaScript Module |

3. **Add the card** to a dashboard.

## Usage

### Minimal YAML

```yaml
type: custom:athletic-layer-card
entity: sensor.athletic_layer_clothing_advice
```

### Full configuration

```yaml
type: custom:athletic-layer-card
entity: sensor.athletic_layer_clothing_advice
name: Athletic Layer           # Card title (default: "Athletic Layer")
show_weather_details: true     # Weather grid with wind, UV, etc. (default: true)
show_rain_chart: true          # 8-hour rain bar chart (default: true)
show_air_quality: true         # AQI, PM2.5, PM10 section (default: true)
show_pollen: true              # Pollen chips inside AQ section (default: true)
show_hourly_advice: true       # Scrollable hourly advice cards (default: true)
```

### Multiple instances

If you have more than one Athletic Layer config entry (e.g. different zones), the
entity prefix is auto-detected from the `entity` you provide. You can also set it
explicitly:

```yaml
type: custom:athletic-layer-card
entity: sensor.athletic_layer_2_clothing_advice
entity_prefix: sensor.athletic_layer_2_
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
