/**
 * Athletic Layer Card – Custom Lovelace card for the AthleticLayer integration.
 *
 * Displays current weather conditions, clothing advice (layers, warnings),
 * an 8-hour rain forecast bar chart, and air-quality / pollen data.
 *
 * Installation
 * ────────────
 * 1. Copy this file to  <config>/www/athletic-layer-card.js
 * 2. In HA → Settings → Dashboards → Resources → Add Resource:
 *      URL:  /local/athletic-layer-card.js
 *      Type: JavaScript Module
 * 3. Add the card to a dashboard (see README for YAML).
 */

const CARD_VERSION = "1.0.2";

/* ── Weather-condition → MDI icon mapping ─────────────────────── */
const CONDITION_ICONS = {
  clear_sky: "mdi:weather-sunny",
  mainly_clear: "mdi:weather-sunny",
  partly_cloudy: "mdi:weather-partly-cloudy",
  overcast: "mdi:cloud",
  fog: "mdi:weather-fog",
  depositing_rime_fog: "mdi:weather-fog",
  light_drizzle: "mdi:weather-partly-rainy",
  moderate_drizzle: "mdi:weather-rainy",
  dense_drizzle: "mdi:weather-rainy",
  light_freezing_drizzle: "mdi:weather-snowy-rainy",
  dense_freezing_drizzle: "mdi:weather-snowy-rainy",
  slight_rain: "mdi:weather-rainy",
  moderate_rain: "mdi:weather-rainy",
  heavy_rain: "mdi:weather-pouring",
  light_freezing_rain: "mdi:weather-snowy-rainy",
  heavy_freezing_rain: "mdi:weather-snowy-rainy",
  slight_snow_fall: "mdi:weather-snowy",
  moderate_snow_fall: "mdi:weather-snowy",
  heavy_snow_fall: "mdi:weather-snowy-heavy",
  snow_grains: "mdi:weather-snowy",
  slight_rain_showers: "mdi:weather-partly-rainy",
  moderate_rain_showers: "mdi:weather-rainy",
  violent_rain_showers: "mdi:weather-pouring",
  slight_snow_showers: "mdi:weather-snowy",
  heavy_snow_showers: "mdi:weather-snowy-heavy",
  thunderstorm: "mdi:weather-lightning",
  thunderstorm_slight_hail: "mdi:weather-lightning-rainy",
  thunderstorm_heavy_hail: "mdi:weather-lightning-rainy",
};

/* ── i18n: card UI translations ───────────────────────────────── */
const CARD_I18N = {
  en: {
    conditions: {
      clear_sky: "Clear sky", mainly_clear: "Mainly clear", partly_cloudy: "Partly cloudy",
      overcast: "Overcast", fog: "Fog", depositing_rime_fog: "Rime fog",
      light_drizzle: "Light drizzle", moderate_drizzle: "Drizzle", dense_drizzle: "Dense drizzle",
      light_freezing_drizzle: "Freezing drizzle", dense_freezing_drizzle: "Dense freezing drizzle",
      slight_rain: "Light rain", moderate_rain: "Rain", heavy_rain: "Heavy rain",
      light_freezing_rain: "Freezing rain", heavy_freezing_rain: "Heavy freezing rain",
      slight_snow_fall: "Light snow", moderate_snow_fall: "Snow", heavy_snow_fall: "Heavy snow",
      snow_grains: "Snow grains", slight_rain_showers: "Light showers",
      moderate_rain_showers: "Showers", violent_rain_showers: "Violent showers",
      slight_snow_showers: "Snow showers", heavy_snow_showers: "Heavy snow showers",
      thunderstorm: "Thunderstorm", thunderstorm_slight_hail: "Thunderstorm + hail",
      thunderstorm_heavy_hail: "Thunderstorm + heavy hail",
    },
    compass: { N:"N", NNE:"NNE", NE:"NE", ENE:"ENE", E:"E", ESE:"ESE", SE:"SE", SSE:"SSE",
               S:"S", SSW:"SSW", SW:"SW", WSW:"WSW", W:"W", WNW:"WNW", NW:"NW", NNW:"NNW" },
    aqi: { good:"Good", fair:"Fair", moderate:"Moderate", poor:"Poor", very_poor:"Very poor", hazardous:"Hazardous", na:"N/A" },
    ui: {
      feels: "Feels", updated: "Updated", mm_total: "mm total",
      tile_wind: "Wind", tile_gusts: "Gusts", tile_humidity: "Humidity", tile_uv: "UV",
      tile_rain: "Rain", tile_rain_prob: "Rain prob.", tile_clouds: "Clouds",
      tile_sunrise: "Sunrise", tile_sunset: "Sunset",
      sect_clothing: "Clothing Advice", sect_layers: "Layers", sect_alerts: "Alerts",
      sect_rain: "Rain Forecast 8 h", sect_air_quality: "Air Quality", sect_hourly: "Hourly Advice",
      pollen_grass: "Grass", pollen_birch: "Birch", pollen_alder: "Alder",
      pollen_mugwort: "Mugwort", pollen_olive: "Olive", pollen_ragweed: "Ragweed",
      layer_base: "Base", layer_mid: "Mid", layer_outer: "Outer",
      layer_bottoms: "Bottoms", layer_accessories: "Accessories",
    },
    sports: { running: "Running", cycling: "Cycling", hiking: "Hiking", walking: "Walking" },
  },
  de: {
    conditions: {
      clear_sky: "Klarer Himmel", mainly_clear: "Überwiegend klar", partly_cloudy: "Teilweise bewölkt",
      overcast: "Bedeckt", fog: "Nebel", depositing_rime_fog: "Gefrierender Nebel",
      light_drizzle: "Leichter Nieselregen", moderate_drizzle: "Nieselregen", dense_drizzle: "Starker Nieselregen",
      light_freezing_drizzle: "Leichter gefrierender Nieselregen", dense_freezing_drizzle: "Starker gefrierender Nieselregen",
      slight_rain: "Leichter Regen", moderate_rain: "Regen", heavy_rain: "Starker Regen",
      light_freezing_rain: "Leichter Eisregen", heavy_freezing_rain: "Starker Eisregen",
      slight_snow_fall: "Leichter Schneefall", moderate_snow_fall: "Schneefall", heavy_snow_fall: "Starker Schneefall",
      snow_grains: "Schneegriesel", slight_rain_showers: "Leichte Regenschauer",
      moderate_rain_showers: "Regenschauer", violent_rain_showers: "Heftige Regenschauer",
      slight_snow_showers: "Leichte Schneeschauer", heavy_snow_showers: "Starke Schneeschauer",
      thunderstorm: "Gewitter", thunderstorm_slight_hail: "Gewitter mit leichtem Hagel",
      thunderstorm_heavy_hail: "Gewitter mit starkem Hagel",
    },
    compass: { N:"N", NNE:"NNO", NE:"NO", ENE:"ONO", E:"O", ESE:"OSO", SE:"SO", SSE:"SSO",
               S:"S", SSW:"SSW", SW:"SW", WSW:"WSW", W:"W", WNW:"WNW", NW:"NW", NNW:"NNW" },
    aqi: { good:"Gut", fair:"Mäßig", moderate:"Mittel", poor:"Schlecht", very_poor:"Sehr schlecht", hazardous:"Gefährlich", na:"k. A." },
    ui: {
      feels: "Gefühlt", updated: "Aktualisiert", mm_total: "mm gesamt",
      tile_wind: "Wind", tile_gusts: "Böen", tile_humidity: "Feuchtigkeit", tile_uv: "UV",
      tile_rain: "Regen", tile_rain_prob: "Regenwahrsch.", tile_clouds: "Wolken",
      tile_sunrise: "Sonnenaufgang", tile_sunset: "Sonnenuntergang",
      sect_clothing: "Kleidungsempfehlung", sect_layers: "Schichten", sect_alerts: "Warnungen",
      sect_rain: "Regenvorhersage 8 Std.", sect_air_quality: "Luftqualität", sect_hourly: "Stündliche Empfehlung",
      pollen_grass: "Gräser", pollen_birch: "Birke", pollen_alder: "Erle",
      pollen_mugwort: "Beifuß", pollen_olive: "Olive", pollen_ragweed: "Ambrosia",
      layer_base: "Basis", layer_mid: "Mittel", layer_outer: "Außen",
      layer_bottoms: "Hose", layer_accessories: "Zubehör",
    },
    sports: { running: "Laufen", cycling: "Radfahren", hiking: "Wandern", walking: "Gehen" },
  },
  es: {
    conditions: {
      clear_sky: "Cielo despejado", mainly_clear: "Mayormente despejado", partly_cloudy: "Parcialmente nublado",
      overcast: "Nublado", fog: "Niebla", depositing_rime_fog: "Niebla con escarcha",
      light_drizzle: "Llovizna ligera", moderate_drizzle: "Llovizna", dense_drizzle: "Llovizna densa",
      light_freezing_drizzle: "Llovizna helada ligera", dense_freezing_drizzle: "Llovizna helada densa",
      slight_rain: "Lluvia ligera", moderate_rain: "Lluvia", heavy_rain: "Lluvia fuerte",
      light_freezing_rain: "Lluvia helada ligera", heavy_freezing_rain: "Lluvia helada fuerte",
      slight_snow_fall: "Nevada ligera", moderate_snow_fall: "Nevada", heavy_snow_fall: "Nevada fuerte",
      snow_grains: "Granos de nieve", slight_rain_showers: "Chubascos ligeros",
      moderate_rain_showers: "Chubascos", violent_rain_showers: "Chubascos violentos",
      slight_snow_showers: "Chubascos de nieve", heavy_snow_showers: "Chubascos de nieve fuertes",
      thunderstorm: "Tormenta eléctrica", thunderstorm_slight_hail: "Tormenta con granizo ligero",
      thunderstorm_heavy_hail: "Tormenta con granizo fuerte",
    },
    compass: { N:"N", NNE:"NNE", NE:"NE", ENE:"ENE", E:"E", ESE:"ESE", SE:"SE", SSE:"SSE",
               S:"S", SSW:"SSO", SW:"SO", WSW:"OSO", W:"O", WNW:"ONO", NW:"NO", NNW:"NNO" },
    aqi: { good:"Buena", fair:"Aceptable", moderate:"Moderada", poor:"Mala", very_poor:"Muy mala", hazardous:"Peligrosa", na:"N/D" },
    ui: {
      feels: "Sensación", updated: "Actualizado", mm_total: "mm total",
      tile_wind: "Viento", tile_gusts: "Rachas", tile_humidity: "Humedad", tile_uv: "UV",
      tile_rain: "Lluvia", tile_rain_prob: "Prob. lluvia", tile_clouds: "Nubes",
      tile_sunrise: "Amanecer", tile_sunset: "Atardecer",
      sect_clothing: "Consejo de vestimenta", sect_layers: "Capas", sect_alerts: "Alertas",
      sect_rain: "Previsión lluvia 8 h", sect_air_quality: "Calidad del aire", sect_hourly: "Consejo por hora",
      pollen_grass: "Gramíneas", pollen_birch: "Abedul", pollen_alder: "Aliso",
      pollen_mugwort: "Artemisa", pollen_olive: "Olivo", pollen_ragweed: "Ambrosía",
      layer_base: "Base", layer_mid: "Intermedia", layer_outer: "Exterior",
      layer_bottoms: "Pantalón", layer_accessories: "Accesorios",
    },
    sports: { running: "Correr", cycling: "Ciclismo", hiking: "Senderismo", walking: "Caminar" },
  },
  fr: {
    conditions: {
      clear_sky: "Ciel dégagé", mainly_clear: "Généralement dégagé", partly_cloudy: "Partiellement nuageux",
      overcast: "Couvert", fog: "Brouillard", depositing_rime_fog: "Brouillard givrant",
      light_drizzle: "Bruine légère", moderate_drizzle: "Bruine", dense_drizzle: "Bruine dense",
      light_freezing_drizzle: "Bruine verglaçante légère", dense_freezing_drizzle: "Bruine verglaçante dense",
      slight_rain: "Pluie légère", moderate_rain: "Pluie", heavy_rain: "Pluie forte",
      light_freezing_rain: "Pluie verglaçante légère", heavy_freezing_rain: "Pluie verglaçante forte",
      slight_snow_fall: "Légère chute de neige", moderate_snow_fall: "Chute de neige", heavy_snow_fall: "Forte chute de neige",
      snow_grains: "Grains de neige", slight_rain_showers: "Averses légères",
      moderate_rain_showers: "Averses", violent_rain_showers: "Averses violentes",
      slight_snow_showers: "Averses de neige légères", heavy_snow_showers: "Averses de neige fortes",
      thunderstorm: "Orage", thunderstorm_slight_hail: "Orage avec grêle légère",
      thunderstorm_heavy_hail: "Orage avec forte grêle",
    },
    compass: { N:"N", NNE:"NNE", NE:"NE", ENE:"ENE", E:"E", ESE:"ESE", SE:"SE", SSE:"SSE",
               S:"S", SSW:"SSO", SW:"SO", WSW:"OSO", W:"O", WNW:"ONO", NW:"NO", NNW:"NNO" },
    aqi: { good:"Bon", fair:"Correct", moderate:"Modéré", poor:"Mauvais", very_poor:"Très mauvais", hazardous:"Dangereux", na:"N/D" },
    ui: {
      feels: "Ressenti", updated: "Mis à jour", mm_total: "mm au total",
      tile_wind: "Vent", tile_gusts: "Rafales", tile_humidity: "Humidité", tile_uv: "UV",
      tile_rain: "Pluie", tile_rain_prob: "Prob. pluie", tile_clouds: "Nuages",
      tile_sunrise: "Lever soleil", tile_sunset: "Coucher soleil",
      sect_clothing: "Conseil vestimentaire", sect_layers: "Couches", sect_alerts: "Alertes",
      sect_rain: "Prévision pluie 8 h", sect_air_quality: "Qualité de l'air", sect_hourly: "Conseil horaire",
      pollen_grass: "Graminées", pollen_birch: "Bouleau", pollen_alder: "Aulne",
      pollen_mugwort: "Armoise", pollen_olive: "Olivier", pollen_ragweed: "Ambroisie",
      layer_base: "Base", layer_mid: "Intermédiaire", layer_outer: "Extérieure",
      layer_bottoms: "Pantalon", layer_accessories: "Accessoires",
    },
    sports: { running: "Course", cycling: "Cyclisme", hiking: "Randonnée", walking: "Marche" },
  },
  nl: {
    conditions: {
      clear_sky: "Onbewolkt", mainly_clear: "Overwegend helder", partly_cloudy: "Halfbewolkt",
      overcast: "Bewolkt", fog: "Mist", depositing_rime_fog: "Aanvriezende mist",
      light_drizzle: "Lichte motregen", moderate_drizzle: "Motregen", dense_drizzle: "Dichte motregen",
      light_freezing_drizzle: "Lichte ijzel", dense_freezing_drizzle: "Dichte ijzel",
      slight_rain: "Lichte regen", moderate_rain: "Regen", heavy_rain: "Zware regen",
      light_freezing_rain: "Lichte ijsregen", heavy_freezing_rain: "Zware ijsregen",
      slight_snow_fall: "Lichte sneeuwval", moderate_snow_fall: "Sneeuwval", heavy_snow_fall: "Zware sneeuwval",
      snow_grains: "Sneeuwkorrels", slight_rain_showers: "Lichte regenbuien",
      moderate_rain_showers: "Regenbuien", violent_rain_showers: "Hevige regenbuien",
      slight_snow_showers: "Lichte sneeuwbuien", heavy_snow_showers: "Zware sneeuwbuien",
      thunderstorm: "Onweer", thunderstorm_slight_hail: "Onweer met lichte hagel",
      thunderstorm_heavy_hail: "Onweer met zware hagel",
    },
    compass: { N:"N", NNE:"NNO", NE:"NO", ENE:"ONO", E:"O", ESE:"OZO", SE:"ZO", SSE:"ZZO",
               S:"Z", SSW:"ZZW", SW:"ZW", WSW:"WZW", W:"W", WNW:"WNW", NW:"NW", NNW:"NNW" },
    aqi: { good:"Goed", fair:"Redelijk", moderate:"Matig", poor:"Slecht", very_poor:"Zeer slecht", hazardous:"Gevaarlijk", na:"n.v.t." },
    ui: {
      feels: "Gevoels", updated: "Bijgewerkt", mm_total: "mm totaal",
      tile_wind: "Wind", tile_gusts: "Windstoten", tile_humidity: "Vochtigheid", tile_uv: "UV",
      tile_rain: "Regen", tile_rain_prob: "Regenkans", tile_clouds: "Wolken",
      tile_sunrise: "Zonsopkomst", tile_sunset: "Zonsondergang",
      sect_clothing: "Kledingadvies", sect_layers: "Lagen", sect_alerts: "Waarschuwingen",
      sect_rain: "Neerslagverwachting 8 u", sect_air_quality: "Luchtkwaliteit", sect_hourly: "Advies per uur",
      pollen_grass: "Gras", pollen_birch: "Berk", pollen_alder: "Els",
      pollen_mugwort: "Bijvoet", pollen_olive: "Olijf", pollen_ragweed: "Ambrosia",
      layer_base: "Basis", layer_mid: "Midden", layer_outer: "Buiten",
      layer_bottoms: "Broek", layer_accessories: "Accessoires",
    },
    sports: { running: "Hardlopen", cycling: "Fietsen", hiking: "Wandelen", walking: "Wandelen" },
  },
};

/* ── AQI colour bands (European AQI) ─────────────────────────── */
function aqiColor(aqi) {
  if (aqi == null) return "var(--secondary-text-color)";
  if (aqi <= 20) return "#50c878";
  if (aqi <= 40) return "#a3d65c";
  if (aqi <= 60) return "#ffd700";
  if (aqi <= 80) return "#ff8c00";
  if (aqi <= 100) return "#ff4500";
  return "#8b0000";
}

/* ── Layer icon mapping ───────────────────────────────────────── */
const LAYER_ICONS = {
  base: "mdi:tshirt-crew",
  mid: "mdi:layers-outline",
  outer: "mdi:jacket-outline",
  bottoms: "mdi:human-male",
  accessories: "mdi:hat-fedora",
};

/* ── Helpers ──────────────────────────────────────────────────── */
function entityState(hass, id) {
  const e = hass.states[id];
  return e ? e.state : undefined;
}
function entityNumeric(hass, id) {
  const v = entityState(hass, id);
  return v != null && v !== "unknown" && v !== "unavailable" ? Number(v) : null;
}
function entityAttr(hass, id, attr) {
  const e = hass.states[id];
  return e && e.attributes ? e.attributes[attr] : undefined;
}

/* ── Card class ───────────────────────────────────────────────── */
class AthleticLayerCard extends HTMLElement {
  set hass(hass) {
    const prevLang = this._hass ? this._hass.language : undefined;
    this._hass = hass;
    if (!this._rendered) {
      this._render();
      this._rendered = true;
    } else {
      this._update();
    }
    // Tell the backend the current frontend language so advice matches.
    // Fire on initial load AND on any language change.
    const newLang = hass.language;
    if (newLang && this._config && (!this._langSent || (prevLang && prevLang !== newLang))) {
      this._langSent = true;
      const lang = newLang.split("-")[0].toLowerCase();
      this._hass.callWS({
        type: "fire_event",
        event_type: "athletic_layer_language_changed",
        event_data: { language: lang },
      }).catch(() => {});
    }
  }

  setConfig(config) {
    if (!config.zone && !config.entity) {
      throw new Error("Please define a 'zone' (e.g. 'home') or an 'entity' (the clothing_advice sensor).");
    }
    const zone = config.zone || null;
    const entity = config.entity || (zone ? `sensor.${zone}_clothing_advice` : undefined);
    const prefix = config.entity_prefix || (zone ? `sensor.${zone}_` : this._guessPrefix(entity));
    this._config = {
      zone: zone,
      entity: entity,
      name: config.name || "Athletic Layer",
      show_hourly_advice: config.show_hourly_advice !== false,
      show_rain_chart: config.show_rain_chart !== false,
      show_air_quality: config.show_air_quality !== false,
      show_pollen: config.show_pollen !== false,
      show_weather_details: config.show_weather_details !== false,
      entity_prefix: prefix,
    };
    this._rendered = false;
  }

  _guessPrefix(entity) {
    // "sensor.home_clothing_advice" → "sensor.home_"
    const idx = entity.lastIndexOf("clothing_advice");
    return idx > 0 ? entity.substring(0, idx) : "sensor.home_";
  }

  _e(key) {
    return this._config.entity_prefix + key;
  }

  /* ── i18n helpers ──────────────────────────────────────── */
  _lang() {
    if (!this._hass) return "en";
    // Use the HA frontend language (updates immediately when user changes profile)
    const lang = (this._hass.language || "en").split("-")[0].toLowerCase();
    if (CARD_I18N[lang]) return lang;
    // Fall back to the sensor's resolved language
    const sensorLang = entityAttr(this._hass, this._config.entity, "language");
    if (sensorLang && CARD_I18N[sensorLang]) return sensorLang;
    return "en";
  }

  _i18n() {
    return CARD_I18N[this._lang()];
  }

  /** Look up a UI string key (e.g. "tile_wind"). */
  _t(key) {
    return this._i18n().ui[key] || CARD_I18N.en.ui[key] || key;
  }

  /** Translate a weather condition key. */
  _tc(condKey) {
    return this._i18n().conditions[condKey] || CARD_I18N.en.conditions[condKey] || condKey || "—";
  }

  /** Translate a compass direction from English (N, NNE, …). */
  _twd(dir) {
    if (!dir) return "";
    return this._i18n().compass[dir] || CARD_I18N.en.compass[dir] || dir;
  }

  /** Translate AQI numeric value to a label. */
  _taqi(aqi) {
    const a = this._i18n().aqi;
    if (aqi == null) return a.na;
    if (aqi <= 20) return a.good;
    if (aqi <= 40) return a.fair;
    if (aqi <= 60) return a.moderate;
    if (aqi <= 80) return a.poor;
    if (aqi <= 100) return a.very_poor;
    return a.hazardous;
  }

  getCardSize() {
    return 8;
  }

  static getStubConfig() {
    return { zone: "home" };
  }

  /* ── Initial render ──────────────────────────────────────── */
  _render() {
    if (!this._config || !this._hass) return;
    this.innerHTML = "";
    const shadow = this.attachShadow
      ? this.shadowRoot || this.attachShadow({ mode: "open" })
      : this;

    const card = document.createElement("ha-card");
    card.innerHTML = `
      <style>${this._styles()}</style>
      <div class="al-card">
        <div class="al-header" id="al-header"></div>
        <div class="al-weather-grid" id="al-weather"></div>
        <div class="al-section" id="al-advice-section"></div>
        <div class="al-section" id="al-layers-section"></div>
        <div class="al-section" id="al-warnings-section"></div>
        <div class="al-section" id="al-rain-section"></div>
        <div class="al-section" id="al-aq-section"></div>
        <div class="al-section" id="al-hourly-section"></div>
        <div class="al-footer">Athletic Layer v${CARD_VERSION}</div>
      </div>`;
    shadow.appendChild(card);
    this._card = card;
    this._update();
  }

  /* ── Reactive update ─────────────────────────────────────── */
  _update() {
    if (!this._card || !this._hass) return;
    const h = this._hass;
    const c = this._config;
    const $ = (id) => this._card.querySelector(`#${id}`);

    /* ── Header ─────────────────────────────────────────────── */
    const condition = entityState(h, this._e("weather_condition"));
    const condIcon = CONDITION_ICONS[condition] || "mdi:weather-cloudy";
    const condLabel = this._tc(condition);
    const temp = entityNumeric(h, this._e("temperature"));
    const feelsLike = entityNumeric(h, this._e("feels_like_temperature"));
    const location = entityAttr(h, c.entity, "location") || "";

    $("al-header").innerHTML = `
      <div class="al-header-row">
        <div class="al-header-left">
          <ha-icon icon="${condIcon}" class="al-cond-icon"></ha-icon>
          <div class="al-header-temp">
            <span class="al-temp">${temp != null ? temp.toFixed(1) + "°" : "—"}</span>
            <span class="al-feels-like">${feelsLike != null ? this._t("feels") + " " + feelsLike.toFixed(1) + "°" : ""}</span>
          </div>
        </div>
        <div class="al-header-right">
          <span class="al-title">${c.name}</span>
          <span class="al-condition">${condLabel}</span>
          ${location ? `<span class="al-location">${this._esc(location)}</span>` : ""}
        </div>
      </div>`;

    /* ── Weather details grid ──────────────────────────────── */
    if (c.show_weather_details) {
      const wind = entityNumeric(h, this._e("wind_speed"));
      const gusts = entityNumeric(h, this._e("wind_gusts"));
      const dir = entityState(h, this._e("wind_direction"));
      const hum = entityNumeric(h, this._e("humidity"));
      const uv = entityNumeric(h, this._e("uv_index"));
      const precip = entityNumeric(h, this._e("precipitation"));
      const precipP = entityNumeric(h, this._e("precipitation_probability"));
      const cloud = entityNumeric(h, this._e("cloud_cover"));
      const sunrise = entityState(h, this._e("sunrise"));
      const sunset = entityState(h, this._e("sunset"));
      const windUnit = entityAttr(h, this._e("wind_speed"), "unit_of_measurement") || "km/h";
      const precipUnit = entityAttr(h, this._e("precipitation"), "unit_of_measurement") || "mm";

      $("al-weather").innerHTML = `
        ${this._weatherTile("mdi:weather-windy", this._t("tile_wind"), wind != null ? `${wind.toFixed(0)} ${windUnit} ${this._twd(dir)}` : "—")}
        ${this._weatherTile("mdi:weather-windy-variant", this._t("tile_gusts"), gusts != null ? `${gusts.toFixed(0)} ${windUnit}` : "—")}
        ${this._weatherTile("mdi:water-percent", this._t("tile_humidity"), hum != null ? `${hum}%` : "—")}
        ${this._weatherTile("mdi:sun-wireless", this._t("tile_uv"), uv != null ? uv.toFixed(1) : "—")}
        ${this._weatherTile("mdi:weather-rainy", this._t("tile_rain"), precip != null ? `${precip.toFixed(1)} ${precipUnit}` : "—")}
        ${this._weatherTile("mdi:cloud-percent-outline", this._t("tile_rain_prob"), precipP != null ? `${precipP}%` : "—")}
        ${this._weatherTile("mdi:cloud", this._t("tile_clouds"), cloud != null ? `${cloud}%` : "—")}
        ${this._weatherTile("mdi:weather-sunset-up", this._t("tile_sunrise"), sunrise && sunrise !== "unknown" ? sunrise : "—")}
        ${this._weatherTile("mdi:weather-sunset-down", this._t("tile_sunset"), sunset && sunset !== "unknown" ? sunset : "—")}
      `;
    } else {
      $("al-weather").innerHTML = "";
    }

    /* ── Advice text ───────────────────────────────────────── */
    const adviceState = entityState(h, c.entity);
    const detailed = entityAttr(h, c.entity, "detailed_advice");
    const generated = entityAttr(h, c.entity, "generated_at");
    const sport = entityAttr(h, c.entity, "sport") || "";
    const sportLabel = sport ? (this._i18n().sports[sport] || CARD_I18N.en.sports[sport] || sport.replace("_", " ")) : "";

    $('al-advice-section').innerHTML = (detailed || adviceState)
      ? `<div class="al-sect-title"><ha-icon icon="mdi:tshirt-crew"></ha-icon> ${this._t('sect_clothing')}${sportLabel ? ` <span class="al-sport-badge">${this._esc(sportLabel)}</span>` : ''}</div>
         <div class="al-advice-text">${this._esc(detailed || adviceState)}</div>
         ${generated ? `<div class="al-generated-at">${this._t('updated')} ${this._esc(generated)}</div>` : ''}`
      : "";

    /* ── Layer breakdown ───────────────────────────────────── */
    const layers = entityAttr(h, c.entity, "layers");
    if (layers && typeof layers === "object") {
      const items = Object.entries(layers)
        .filter(([, v]) => v && v !== "none")
        .map(
          ([k, v]) => `
          <div class="al-layer-row">
            <ha-icon icon="${LAYER_ICONS[k] || "mdi:hanger"}" class="al-layer-icon"></ha-icon>
            <span class="al-layer-label">${this._t("layer_" + k) || this._capitalize(k)}</span>
            <span class="al-layer-value">${this._esc(this._formatLayerValue(v))}</span>
          </div>`
        )
        .join("");
      $("al-layers-section").innerHTML = items
        ? `<div class="al-sect-title"><ha-icon icon="mdi:layers-triple"></ha-icon> ${this._t("sect_layers")}</div>${items}`
        : "";
    } else {
      $("al-layers-section").innerHTML = "";
    }

    /* ── Warnings & health ─────────────────────────────────── */
    const warnings = entityAttr(h, c.entity, "warnings") || [];
    const healthAdj = entityAttr(h, c.entity, "health_adjustments") || [];
    const allWarnings = [...warnings, ...healthAdj];
    if (allWarnings.length) {
      $("al-warnings-section").innerHTML = `
        <div class="al-sect-title al-warn-title"><ha-icon icon="mdi:alert-outline"></ha-icon> ${this._t("sect_alerts")}</div>
        ${allWarnings.map((w) => `<div class="al-warning">${this._esc(w)}</div>`).join("")}`;
    } else {
      $("al-warnings-section").innerHTML = "";
    }

    /* ── Rain forecast chart ───────────────────────────────── */
    if (c.show_rain_chart) {
      const forecast = entityAttr(h, this._e("rainfall_forecast_8h"), "hourly_forecast");
      if (forecast && forecast.length) {
        const maxRain = Math.max(...forecast.map((h) => h.rain_mm || 0), 0.5);
        const bars = forecast
          .map((hr) => {
            const pct = ((hr.rain_mm || 0) / maxRain) * 100;
            const time = hr.time ? hr.time.split("T").pop().substring(0, 5) : "";
            return `
            <div class="al-rain-col">
              <span class="al-rain-val">${(hr.rain_mm || 0).toFixed(1)}</span>
              <div class="al-rain-bar-bg"><div class="al-rain-bar" style="height:${pct}%"></div></div>
              <span class="al-rain-prob">${hr.precipitation_probability ?? "—"}%</span>
              <span class="al-rain-time">${time}</span>
            </div>`;
          })
          .join("");
        const total = entityNumeric(h, this._e("rainfall_forecast_8h"));
        $("al-rain-section").innerHTML = `
          <div class="al-sect-title"><ha-icon icon="mdi:weather-pouring"></ha-icon> ${this._t("sect_rain")}
            <span class="al-rain-total">${total != null ? total.toFixed(1) + " " + this._t("mm_total") : ""}</span>
          </div>
          <div class="al-rain-chart">${bars}</div>`;
      } else {
        $("al-rain-section").innerHTML = "";
      }
    } else {
      $("al-rain-section").innerHTML = "";
    }

    /* ── Air quality & pollen ──────────────────────────────── */
    if (c.show_air_quality) {
      const aqi = entityNumeric(h, this._e("air_quality_index"));
      const pm25 = entityNumeric(h, this._e("pm25"));
      const pm10 = entityNumeric(h, this._e("pm10"));

      let pollenHtml = "";
      if (c.show_pollen) {
        const pollenKeys = ["pollen_grass", "pollen_birch", "pollen_alder", "pollen_mugwort", "pollen_olive", "pollen_ragweed"];
        const pollenItems = pollenKeys
          .map((k) => {
            const v = entityNumeric(h, this._e(k));
            return v != null && v > 0
              ? `<span class="al-pollen-chip">${this._t(k)}: ${v}</span>`
              : null;
          })
          .filter(Boolean)
          .join("");
        if (pollenItems) {
          pollenHtml = `<div class="al-pollen-row">${pollenItems}</div>`;
        }
      }

      if (aqi != null || pm25 != null || pm10 != null || pollenHtml) {
        $("al-aq-section").innerHTML = `
          <div class="al-sect-title"><ha-icon icon="mdi:air-filter"></ha-icon> ${this._t("sect_air_quality")}</div>
          <div class="al-aq-row">
            ${aqi != null ? `<div class="al-aq-badge" style="border-color:${aqiColor(aqi)}">
              <span class="al-aq-val" style="color:${aqiColor(aqi)}">${aqi}</span>
              <span class="al-aq-label">${this._taqi(aqi)}</span>
            </div>` : ""}
            ${pm25 != null ? this._aqTile("PM2.5", pm25.toFixed(1), "µg/m³") : ""}
            ${pm10 != null ? this._aqTile("PM10", pm10.toFixed(1), "µg/m³") : ""}
          </div>
          ${pollenHtml}`;
      } else {
        $("al-aq-section").innerHTML = "";
      }
    } else {
      $("al-aq-section").innerHTML = "";
    }

    /* ── Hourly advice scroll ──────────────────────────────── */
    if (c.show_hourly_advice) {
      const hourly = entityAttr(h, c.entity, "advice_hourly");
      if (hourly && hourly.length > 1) {
        const cards = hourly
          .slice(1) // skip "now" — it's shown above
          .map((hr) => {
            const t = hr.time ? hr.time.split("T").pop().substring(0, 5) : "";
            const hTemp = hr.temperature != null ? `${Number(hr.temperature).toFixed(0)}°` : "";
            // Use cloud coverage for icon if available
            let hIcon;
            if (typeof hr.cloud_coverage === "number") {
              const cloud = hr.cloud_coverage;
              if (cloud < 20) {
                hIcon = CONDITION_ICONS["clear_sky"] || "mdi:weather-sunny";
              } else if (cloud < 50) {
                hIcon = CONDITION_ICONS["mainly_clear"] || "mdi:weather-partly-cloudy";
              } else if (cloud < 85) {
                hIcon = CONDITION_ICONS["partly_cloudy"] || "mdi:weather-cloudy";
              } else {
                hIcon = CONDITION_ICONS["overcast"] || "mdi:cloud";
              }
            } else {
              const hCode = hr.weather_condition || hr.weather_code;
              hIcon = CONDITION_ICONS[hCode] || "mdi:weather-cloudy";
            }
            const summary = hr.summary || hr.short_summary || "";
            const hLayers = hr.layers || {};
            const layerLine = Object.entries(hLayers)
              .filter(([, v]) => v && v !== "none")
              .map(([k, v]) => `${this._t("layer_" + k) || this._capitalize(k)}: ${this._formatLayerValue(v)}`)
              .join(" · ");
            return `
            <div class="al-hourly-card">
              <div class="al-hc-time">${t} ${hTemp}</div>
              <ha-icon icon="${hIcon}" class="al-hc-icon"></ha-icon>
              ${summary ? `<div class="al-hc-summary">${this._esc(summary)}</div>` : ""}
              ${layerLine ? `<div class="al-hc-layers">${this._esc(layerLine)}</div>` : ""}
            </div>`;
          })
          .join("");
        $("al-hourly-section").innerHTML = `
          <div class="al-sect-title"><ha-icon icon="mdi:clock-outline"></ha-icon> ${this._t("sect_hourly")}</div>
          <div class="al-hourly-scroll">${cards}</div>`;
      } else {
        $("al-hourly-section").innerHTML = "";
      }
    } else {
      $("al-hourly-section").innerHTML = "";
    }
  }

  /* ── Sub-renderers ──────────────────────────────────────── */

  _weatherTile(icon, label, value) {
    return `
      <div class="al-wt">
        <ha-icon icon="${icon}" class="al-wt-icon"></ha-icon>
        <span class="al-wt-val">${value}</span>
        <span class="al-wt-label">${label}</span>
      </div>`;
  }

  _aqTile(label, value, unit) {
    return `
      <div class="al-aq-tile">
        <span class="al-aq-tile-val">${value}</span>
        <span class="al-aq-tile-unit">${unit}</span>
        <span class="al-aq-tile-label">${label}</span>
      </div>`;
  }

  _formatLayerValue(v) {
    if (Array.isArray(v)) return v.join(", ");
    if (typeof v === "string") return v.replace(/_/g, " ");
    return String(v);
  }

  _capitalize(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  _esc(s) {
    if (!s) return "";
    const d = document.createElement("div");
    d.textContent = String(s);
    return d.innerHTML;
  }

  /* ── Styles ─────────────────────────────────────────────── */
  _styles() {
    return `
      :host { display: block; }
      .al-card {
        padding: 16px;
        font-family: var(--paper-font-body1_-_font-family, sans-serif);
        color: var(--primary-text-color);
      }

      /* ── Header ────────────────────────────────────────── */
      .al-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }
      .al-header-left {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      .al-cond-icon {
        --mdc-icon-size: 48px;
        color: var(--state-icon-color, var(--paper-item-icon-color));
      }
      .al-header-temp {
        display: flex;
        flex-direction: column;
      }
      .al-temp {
        font-size: 2rem;
        font-weight: 600;
        line-height: 1.1;
      }
      .al-feels-like {
        font-size: 0.85rem;
        color: var(--secondary-text-color);
      }
      .al-header-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        text-align: right;
      }
      .al-title {
        font-size: 1.1rem;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      .al-condition {
        font-size: 0.9rem;
        color: var(--secondary-text-color);
      }
      .al-location {
        font-size: 0.78rem;
        color: var(--secondary-text-color);
        opacity: 0.7;
      }

      /* ── Weather grid ──────────────────────────────────── */
      .al-weather-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 14px;
      }
      .al-wt {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 6px 4px;
        background: var(--card-background-color, var(--ha-card-background));
        border-radius: 8px;
        border: 1px solid var(--divider-color, #e0e0e0);
      }
      .al-wt-icon {
        --mdc-icon-size: 20px;
        color: var(--state-icon-color, var(--paper-item-icon-color));
        margin-bottom: 2px;
      }
      .al-wt-val {
        font-size: 0.88rem;
        font-weight: 500;
      }
      .al-wt-label {
        font-size: 0.72rem;
        color: var(--secondary-text-color);
      }

      /* ── Sections ──────────────────────────────────────── */
      .al-section { margin-bottom: 10px; }
      .al-sect-title {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.92rem;
        font-weight: 600;
        margin-bottom: 6px;
        color: var(--primary-text-color);
      }
      .al-sect-title ha-icon {
        --mdc-icon-size: 18px;
        color: var(--state-icon-color, var(--paper-item-icon-color));
      }
      .al-sport-badge {
        font-size: 0.78rem;
        font-weight: 500;
        padding: 1px 8px;
        border-radius: 10px;
        background: var(--primary-color, #03a9f4);
        color: var(--text-primary-color, #fff);
        margin-left: 4px;
      }

      /* ── Advice text ───────────────────────────────────── */
      .al-advice-text {
        font-size: 0.9rem;
        line-height: 1.5;
        padding: 10px 12px;
        background: var(--card-background-color, var(--ha-card-background));
        border-radius: 8px;
        border-left: 3px solid var(--primary-color, #03a9f4);
      }
      .al-generated-at {
        font-size: 0.72rem;
        color: var(--secondary-text-color);
        opacity: 0.6;
        margin-top: 4px;
        text-align: right;
      }

      /* ── Layers ────────────────────────────────────────── */
      .al-layer-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 0;
        border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.08));
      }
      .al-layer-row:last-child { border-bottom: none; }
      .al-layer-icon {
        --mdc-icon-size: 20px;
        color: var(--state-icon-color, var(--paper-item-icon-color));
        flex-shrink: 0;
      }
      .al-layer-label {
        font-size: 0.82rem;
        font-weight: 500;
        min-width: 80px;
      }
      .al-layer-value {
        font-size: 0.82rem;
        color: var(--secondary-text-color);
      }

      /* ── Warnings ──────────────────────────────────────── */
      .al-warn-title { color: var(--error-color, #db4437); }
      .al-warning {
        font-size: 0.85rem;
        padding: 6px 10px;
        margin-bottom: 4px;
        background: rgba(219, 68, 55, 0.08);
        border-radius: 6px;
        border-left: 3px solid var(--error-color, #db4437);
      }

      /* ── Rain chart ────────────────────────────────────── */
      .al-rain-total {
        font-size: 0.76rem;
        font-weight: 400;
        margin-left: auto;
        color: var(--secondary-text-color);
      }
      .al-rain-chart {
        display: flex;
        gap: 4px;
        align-items: flex-end;
        height: 120px;
      }
      .al-rain-col {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 100%;
        justify-content: flex-end;
      }
      .al-rain-val {
        font-size: 0.68rem;
        color: var(--secondary-text-color);
        margin-bottom: 2px;
      }
      .al-rain-bar-bg {
        width: 100%;
        max-width: 28px;
        flex: 1;
        background: var(--divider-color, rgba(0,0,0,.06));
        border-radius: 4px 4px 0 0;
        position: relative;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
      }
      .al-rain-bar {
        width: 100%;
        background: var(--primary-color, #03a9f4);
        border-radius: 4px 4px 0 0;
        min-height: 2px;
        transition: height 0.4s ease;
      }
      .al-rain-prob {
        font-size: 0.65rem;
        color: var(--secondary-text-color);
        margin-top: 2px;
      }
      .al-rain-time {
        font-size: 0.65rem;
        font-weight: 500;
        color: var(--primary-text-color);
      }

      /* ── Air quality ───────────────────────────────────── */
      .al-aq-row {
        display: flex;
        gap: 12px;
        align-items: center;
        flex-wrap: wrap;
      }
      .al-aq-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 8px 14px;
        border: 2px solid;
        border-radius: 10px;
        min-width: 64px;
      }
      .al-aq-val {
        font-size: 1.4rem;
        font-weight: 700;
      }
      .al-aq-label {
        font-size: 0.72rem;
        color: var(--secondary-text-color);
      }
      .al-aq-tile {
        display: flex;
        flex-direction: column;
        align-items: center;
      }
      .al-aq-tile-val {
        font-size: 1rem;
        font-weight: 600;
      }
      .al-aq-tile-unit {
        font-size: 0.65rem;
        color: var(--secondary-text-color);
      }
      .al-aq-tile-label {
        font-size: 0.72rem;
        color: var(--secondary-text-color);
      }
      .al-pollen-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 8px;
      }
      .al-pollen-chip {
        font-size: 0.75rem;
        padding: 3px 8px;
        border-radius: 12px;
        background: rgba(76, 175, 80, 0.12);
        color: var(--primary-text-color);
      }

      /* ── Hourly advice scroll ──────────────────────────── */
      .al-hourly-scroll {
        display: flex;
        gap: 10px;
        overflow-x: auto;
        padding-bottom: 6px;
        scrollbar-width: thin;
      }
      .al-hourly-scroll::-webkit-scrollbar { height: 4px; }
      .al-hourly-scroll::-webkit-scrollbar-thumb {
        background: var(--scrollbar-thumb-color, rgba(0,0,0,.2));
        border-radius: 4px;
      }
      .al-hourly-card {
        flex: 0 0 130px;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 8px 6px;
        border-radius: 10px;
        border: 1px solid var(--divider-color, #e0e0e0);
        background: var(--card-background-color, var(--ha-card-background));
        text-align: center;
      }
      .al-hc-time {
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 4px;
      }
      .al-hc-icon {
        --mdc-icon-size: 24px;
        color: var(--state-icon-color, var(--paper-item-icon-color));
        margin-bottom: 4px;
      }
      .al-hc-summary {
        font-size: 0.72rem;
        color: var(--secondary-text-color);
        line-height: 1.3;
        margin-bottom: 4px;
      }
      .al-hc-layers {
        font-size: 0.68rem;
        color: var(--secondary-text-color);
        line-height: 1.3;
      }

      /* ── Footer ────────────────────────────────────────── */
      .al-footer {
        text-align: right;
        font-size: 0.65rem;
        color: var(--secondary-text-color);
        opacity: 0.4;
        margin-top: 8px;
      }
    `;
  }
}

/* ── Register the card ────────────────────────────────────────── */
customElements.define("athletic-layer-card", AthleticLayerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "athletic-layer-card",
  name: "Athletic Layer",
  description: "Weather conditions and personalized clothing advice for athletes.",
  preview: true,
});

console.info(
  `%c ATHLETIC-LAYER-CARD %c v${CARD_VERSION} `,
  "background:#03a9f4;color:#fff;font-weight:700;padding:2px 6px;border-radius:4px 0 0 4px",
  "background:#444;color:#fff;padding:2px 6px;border-radius:0 4px 4px 0"
);
