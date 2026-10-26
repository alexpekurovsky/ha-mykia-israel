"""Sensors for Kia Ituran vehicles."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import KiaIturanConfigEntry, KiaIturanDataUpdateCoordinator
from .entity import KiaIturanBaseEntity
from .vehicle import KiaVehicle


@dataclass(frozen=True, kw_only=True)
class KiaIturanSensorEntityDescription(SensorEntityDescription):
    """Describes a Kia Ituran sensor."""

    value_fn: Callable[[KiaVehicle], StateType | datetime]
    supported_fn: Callable[[KiaVehicle], bool] = lambda _: True


SENSOR_TYPES: list[KiaIturanSensorEntityDescription] = [
    KiaIturanSensorEntityDescription(
        key="address",
        translation_key="address",
        entity_registry_enabled_default=False,
        value_fn=lambda v: v.address,
    ),
    KiaIturanSensorEntityDescription(
        key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda v: v.battery_level,
        supported_fn=lambda v: v.is_electric_vehicle,
    ),
    KiaIturanSensorEntityDescription(
        key="battery_range",
        translation_key="battery_range",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        value_fn=lambda v: v.battery_range,
        supported_fn=lambda v: v.is_electric_vehicle,
    ),
    KiaIturanSensorEntityDescription(
        key="charging_mode",
        translation_key="charging_mode",
        value_fn=lambda v: v.charging_mode,
        supported_fn=lambda v: v.is_electric_vehicle,
    ),
    KiaIturanSensorEntityDescription(
        key="charging_time_remaining",
        translation_key="charging_time_remaining",
        value_fn=lambda v: v.charging_time_remaining,
        supported_fn=lambda v: v.is_electric_vehicle,
    ),
    KiaIturanSensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=lambda v: v.battery_voltage,
    ),
    KiaIturanSensorEntityDescription(
        key="heading",
        translation_key="heading",
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda v: v.heading,
    ),
    KiaIturanSensorEntityDescription(
        key="last_update_from_vehicle",
        translation_key="last_update_from_vehicle",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda v: v.last_update,
    ),
    KiaIturanSensorEntityDescription(
        key="mileage",
        translation_key="mileage",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=1,
        value_fn=lambda v: v.mileage,
    ),
    KiaIturanSensorEntityDescription(
        key="speed",
        device_class=SensorDeviceClass.SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=0,
        value_fn=lambda v: v.speed,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: KiaIturanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Kia Ituran sensors."""
    coordinator = config_entry.runtime_data

    # Static typed sensors
    async_add_entities(
        KiaIturanSensor(coordinator, plate, description)
        for plate, vehicle in coordinator.data.items()
        for description in SENSOR_TYPES
        if description.supported_fn(vehicle)
    )

    # Dynamic EV diagnostic sensors for any DiagnosticValues code not covered by static sensors
    known_ev: dict[str, set[str]] = {}  # plate -> set of already-created codes

    @callback
    def _add_new_ev_diagnostics() -> None:
        new_entities = []
        for plate, vehicle in coordinator.data.items():
            plate_known = known_ev.setdefault(plate, set())
            for code, info in vehicle.ev_diagnostics.items():
                if code not in plate_known and code not in vehicle.ev_covered_codes:
                    plate_known.add(code)
                    new_entities.append(
                        KiaIturanEVDiagnosticSensor(coordinator, plate, code, info["name"])
                    )
        if new_entities:
            async_add_entities(new_entities)

    _add_new_ev_diagnostics()
    config_entry.async_on_unload(coordinator.async_add_listener(_add_new_ev_diagnostics))


class KiaIturanSensor(KiaIturanBaseEntity, SensorEntity):
    """A Kia Ituran sensor."""

    entity_description: KiaIturanSensorEntityDescription

    def __init__(
        self,
        coordinator: KiaIturanDataUpdateCoordinator,
        license_plate: str,
        description: KiaIturanSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, license_plate, description.key)
        self.entity_description = description

    @property
    @override
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.vehicle)


class KiaIturanEVDiagnosticSensor(KiaIturanBaseEntity, SensorEntity):
    """A dynamic sensor for an EV diagnostic code not covered by a specific typed sensor."""

    def __init__(
        self,
        coordinator: KiaIturanDataUpdateCoordinator,
        license_plate: str,
        code: str,
        name: str,
    ) -> None:
        super().__init__(coordinator, license_plate, f"ev_{code}")
        self._code = code
        self._attr_name = name

    @property
    @override
    def available(self) -> bool:
        return super().available and self._code in self.vehicle.ev_diagnostics

    @property
    @override
    def native_value(self) -> StateType:
        info = self.vehicle.ev_diagnostics.get(self._code)
        return info["value"] if info else None
