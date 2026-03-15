"""Config flow for the AthleticLayer integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_HEALTH_CONDITIONS,
    CONF_SPORT,
    CONF_USER_ID,
    CONF_ZONE,
    DOMAIN,
    HEALTH_CONDITIONS,
    SPORT_RUNNING,
    SPORTS,
)


def _build_options_schema(
    sport_default: str = SPORT_RUNNING,
    health_default: list[str] | None = None,
) -> vol.Schema:
    """Build the form schema for the options flow (zone is fixed after setup)."""
    return vol.Schema(
        {
            vol.Required(CONF_SPORT, default=sport_default): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": s, "label": s.replace("_", " ").title()}
                        for s in SPORTS
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_HEALTH_CONDITIONS, default=health_default or []
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": c, "label": c.replace("_", " ").title()}
                        for c in HEALTH_CONDITIONS
                    ],
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            ),
        }
    )


def _build_schema(
    sport_default: str = SPORT_RUNNING,
    health_default: list[str] | None = None,
    zone_default: str = "zone.home",
) -> vol.Schema:
    """Build the form schema shared by config-flow and options-flow."""
    return vol.Schema(
        {
            vol.Required(CONF_ZONE, default=zone_default): EntitySelector(
                EntitySelectorConfig(domain="zone")
            ),
            vol.Required(CONF_SPORT, default=sport_default): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": s, "label": s.replace("_", " ").title()}
                        for s in SPORTS
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_HEALTH_CONDITIONS, default=health_default or []
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": c, "label": c.replace("_", " ").title()}
                        for c in HEALTH_CONDITIONS
                    ],
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            ),
        }
    )


class AthleticLayerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial configuration flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step."""
        if user_input is not None:
            zone_entity_id = user_input.get(CONF_ZONE, "zone.home")

            # Prevent duplicate entries for the same zone
            await self.async_set_unique_id(zone_entity_id)
            self._abort_if_unique_id_configured()

            # Use the zone's friendly name as the entry title
            zone_state = self.hass.states.get(zone_entity_id)
            zone_name = zone_state.name if zone_state else zone_entity_id
            title = f"Athletic Layer – {zone_name}"

            # Store the user who created this entry for language resolution
            user_id = self.context.get("user_id")
            if user_id:
                user_input[CONF_USER_ID] = user_id

            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return AthleticLayerOptionsFlow(config_entry)


class AthleticLayerOptionsFlow(OptionsFlow):
    """Handle option changes after initial setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Store the config entry reference."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options (zone cannot be changed after setup)."""
        if user_input is not None:
            # Backfill user_id for entries created before it was stored
            merged = {**self._config_entry.data, **user_input}
            if CONF_USER_ID not in merged:
                uid = self.context.get("user_id")
                if uid:
                    merged[CONF_USER_ID] = uid
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data=merged,
            )
            return self.async_create_entry(title="", data={})

        schema = _build_options_schema(
            sport_default=self._config_entry.data.get(CONF_SPORT, SPORT_RUNNING),
            health_default=self._config_entry.data.get(CONF_HEALTH_CONDITIONS, []),
        )
        return self.async_show_form(step_id="init", data_schema=schema)
