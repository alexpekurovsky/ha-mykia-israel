"""Device tracker for Kia Ituran vehicles."""

from typing import override

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import KiaIturanConfigEntry, KiaIturanDataUpdateCoordinator
from .entity import KiaIturanBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: KiaIturanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Kia Ituran tracker from config entry."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        KiaIturanDeviceTracker(coordinator, license_plate)
        for license_plate in coordinator.data
    )


class KiaIturanDeviceTracker(KiaIturanBaseEntity, TrackerEntity):
    """Kia Ituran device tracker."""

    _attr_translation_key = "car"
    _attr_name = None

    def __init__(
        self,
        coordinator: KiaIturanDataUpdateCoordinator,
        license_plate: str,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, license_plate, "device_tracker")

    @property
    @override
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self.vehicle.gps_coordinates[0]

    @property
    @override
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self.vehicle.gps_coordinates[1]
