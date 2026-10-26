"""Binary sensors for Kia Ituran vehicles."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import KiaIturanConfigEntry, KiaIturanDataUpdateCoordinator
from .entity import KiaIturanBaseEntity
from .vehicle import KiaVehicle


@dataclass(frozen=True, kw_only=True)
class KiaIturanBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Kia Ituran binary sensor."""

    value_fn: Callable[[KiaVehicle], bool]
    supported_fn: Callable[[KiaVehicle], bool] = lambda _: True


BINARY_SENSOR_TYPES: list[KiaIturanBinarySensorEntityDescription] = [
    KiaIturanBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda v: v.is_charging,
        supported_fn=lambda v: v.is_electric_vehicle,
    ),
    KiaIturanBinarySensorEntityDescription(
        key="engine",
        translation_key="engine",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda v: v.engine_on,
    ),
    KiaIturanBinarySensorEntityDescription(
        key="locked",
        translation_key="locked",
        device_class=BinarySensorDeviceClass.LOCK,
        # LOCK device class: True = unlocked. Our locked=True means locked, so invert.
        value_fn=lambda v: not v.locked,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: KiaIturanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Kia Ituran binary sensors."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        KiaIturanBinarySensor(coordinator, plate, description)
        for plate, vehicle in coordinator.data.items()
        for description in BINARY_SENSOR_TYPES
        if description.supported_fn(vehicle)
    )


class KiaIturanBinarySensor(KiaIturanBaseEntity, BinarySensorEntity):
    """A Kia Ituran binary sensor."""

    entity_description: KiaIturanBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: KiaIturanDataUpdateCoordinator,
        license_plate: str,
        description: KiaIturanBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, license_plate, description.key)
        self.entity_description = description

    @property
    @override
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.vehicle)
