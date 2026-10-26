"""Config flow for Kia Ituran integration."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
import logging
from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow, ConfigFlowResult

from .api import KiaIturan
from .const import (
    CONF_DEVICE_ID,
    CONF_OTP,
    CONF_PHONE_NUMBER,
    CONF_PLATE_NUMBER,
    CONF_USERNAME,
    DOMAIN,
)
from .exceptions import KiaIturanApiError, KiaIturanAuthError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PHONE_NUMBER): str,
        vol.Required(CONF_PLATE_NUMBER): str,
    }
)

STEP_OTP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OTP): str,
    }
)


class KiaIturanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kia Ituran."""

    _user_info: dict[str, Any]

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step (phone + plate)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_PLATE_NUMBER])
            if self.source != SOURCE_REAUTH:
                self._abort_if_unique_id_configured()

            # Preserve existing device_id on reauth; generate once for new entries.
            device_id = user_input.get(CONF_DEVICE_ID) or uuid.uuid4().hex[:16]
            user_input[CONF_DEVICE_ID] = device_id

            api = KiaIturan(
                phone_number=user_input[CONF_PHONE_NUMBER],
                plate_number=user_input[CONF_PLATE_NUMBER],
                device_id=device_id,
                username=user_input.get(CONF_USERNAME),
            )

            try:
                authenticated = await api.is_authenticated()
                if not authenticated:
                    await api.request_otp()
            except KiaIturanApiError:
                errors["base"] = "cannot_connect"
            except KiaIturanAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception in async_step_user")
                errors["base"] = "unknown"
            else:
                if authenticated:
                    return self.async_create_entry(
                        title=f"Kia {user_input[CONF_PLATE_NUMBER]}",
                        data=user_input,
                    )
                self._user_info = user_input
                return await self.async_step_otp()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_otp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle OTP entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api = KiaIturan(
                phone_number=self._user_info[CONF_PHONE_NUMBER],
                plate_number=self._user_info[CONF_PLATE_NUMBER],
                device_id=self._user_info[CONF_DEVICE_ID],
            )
            try:
                await api.authenticate(user_input[CONF_OTP])
            except KiaIturanApiError:
                errors["base"] = "cannot_connect"
            except KiaIturanAuthError:
                errors["base"] = "invalid_otp"
            except Exception:
                _LOGGER.exception("Unexpected exception in async_step_otp")
                errors["base"] = "unknown"
            else:
                self._user_info[CONF_USERNAME] = api.username or ""
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data=self._user_info
                    )
                return self.async_create_entry(
                    title=f"Kia {self._user_info[CONF_PLATE_NUMBER]}",
                    data=self._user_info,
                )

        return self.async_show_form(
            step_id="otp", data_schema=STEP_OTP_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication."""
        self._user_info = dict(entry_data)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show reauth confirmation before sending OTP."""
        if user_input is not None:
            return await self.async_step_user(self._user_info)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "phone_number": self._user_info[CONF_PHONE_NUMBER]
            },
        )
