"""Base entity for Kia Ituran."""

from typing import override

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KiaIturanDataUpdateCoordinator
from .vehicle import KiaVehicle


class KiaIturanBaseEntity(CoordinatorEntity[KiaIturanDataUpdateCoordinator]):
    """Common base for all Kia Ituran entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KiaIturanDataUpdateCoordinator,
        license_plate: str,
        unique_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._license_plate = license_plate
        self._attr_unique_id = f"{license_plate}-{unique_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.vehicle.license_plate)},
            manufacturer=self.vehicle.make,
            model=self.vehicle.model,
            name=self.vehicle.model,
            serial_number=self.vehicle.license_plate,
        )

    @property
    @override
    def available(self) -> bool:
        return super().available and self._license_plate in self.coordinator.data

    @property
    def vehicle(self) -> KiaVehicle:
        return self.coordinator.data[self._license_plate]
