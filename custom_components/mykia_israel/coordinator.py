"""Coordinator for Kia Ituran."""

from __future__ import annotations

import logging
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KiaIturan
from .const import (
    CONF_DEVICE_ID,
    CONF_PHONE_NUMBER,
    CONF_PLATE_NUMBER,
    CONF_USERNAME,
    DOMAIN,
    UPDATE_INTERVAL,
)
from .exceptions import KiaIturanApiError, KiaIturanAuthError
from .vehicle import KiaVehicle

_LOGGER = logging.getLogger(__name__)

type KiaIturanConfigEntry = ConfigEntry[KiaIturanDataUpdateCoordinator]


class KiaIturanDataUpdateCoordinator(DataUpdateCoordinator[dict[str, KiaVehicle]]):
    """Class to manage fetching Kia Ituran data."""

    config_entry: KiaIturanConfigEntry

    def __init__(self, hass: HomeAssistant, entry: KiaIturanConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.data[CONF_PLATE_NUMBER]}",
            update_interval=UPDATE_INTERVAL,
            config_entry=entry,
        )
        self.api = KiaIturan(
            phone_number=entry.data[CONF_PHONE_NUMBER],
            plate_number=entry.data[CONF_PLATE_NUMBER],
            device_id=entry.data[CONF_DEVICE_ID],
            username=entry.data[CONF_USERNAME],
        )

    @override
    async def _async_update_data(self) -> dict[str, KiaVehicle]:
        """Fetch data from Kia Ituran."""
        try:
            vehicles = await self.api.get_vehicles()
        except KiaIturanApiError as exc:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="api_error"
            ) from exc
        except KiaIturanAuthError as exc:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="auth_error"
            ) from exc

        updated_data = {v.license_plate: v for v in vehicles}
        self._cleanup_removed_vehicles(updated_data)
        return updated_data

    def _cleanup_removed_vehicles(self, data: dict[str, KiaVehicle]) -> None:
        account_vehicles = {(DOMAIN, plate) for plate in data}
        device_registry = dr.async_get(self.hass)
        device_entries = dr.async_entries_for_config_entry(
            device_registry, config_entry_id=self.config_entry.entry_id
        )
        for device in device_entries:
            if not device.identifiers.intersection(account_vehicles):
                device_registry.async_remove_device(device.id)
