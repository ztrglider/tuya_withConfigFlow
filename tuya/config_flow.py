"""Config flow to configure Tuya integration"""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import TUYA_DOMAIN, CONF_COUNTRYCODE, CONF_PLATFORM

_LOGGER = logging.getLogger(__name__)


class TuyaConfigFlow(config_entries.ConfigFlow, domain=TUYA_DOMAIN):
    """Tuya integration config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow"""
        self._username = vol.UNDEFINED
        self._password = vol.UNDEFINED
        self._country_code = vol.UNDEFINED
        self._platform = vol.UNDEFINED

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            self._username = user_input["username"]
            self._password = user_input["password"]
            self._country_code = user_input["country_code"]
            self._platform = user_input["platform"]

            # Steps for login checking and error handling needed here

            return self.async_create_entry(
                title=user_input[CONF_USERNAME],
                data=user_input,
                description_placeholders={"docs_url": "tuya.com"},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_COUNTRYCODE): str,
                    vol.Optional(CONF_PLATFORM, default="tuya"): str,
                }
            ),
            description_placeholders={"docs_url": "tuya.com"},
            errors=errors,
        )

    async def async_step_import(self, user_input):
        """Import a config flow from configuration."""

        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        country_code = user_input[CONF_PASSWORD]
        platform = user_input[CONF_PLATFORM]

        # code for validating login information and error handling needed

        return self.async_create_entry(
            title=f"{username} (from configuration)",
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_COUNTRYCODE: country_code,
                CONF_PLATFORM: platform,
            },
        )
