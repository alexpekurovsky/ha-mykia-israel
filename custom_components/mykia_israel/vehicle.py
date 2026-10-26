"""Vehicle data class for Kia Ituran integration."""

from datetime import datetime
import re
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from .const import (
    ECM_ENGINE_OFF,
    ECM_LOCKED,
    EV_BATTERY_LEVEL_LABELS,
    EV_BATTERY_RANGE_LABELS,
    EV_CHARGING_MODE_LABELS,
    EV_CHARGING_TIME_LABELS,
    IMS_NAMESPACE,
)

_NS = f"{{{IMS_NAMESPACE}}}"
# Matches "Electric Data - {Name} - {Code}" or "{Name} - {Code}"
_LABEL_RE = re.compile(r"^(?:Electric Data - )?(?P<name>.*?) - (?P<code>\d+)$")


class KiaVehicle:
    """Represents a Kia vehicle with location and status data."""

    def __init__(
        self,
        veh_xml: ET.Element,
        ecm_codes: set[str],
        electric_data_xml: ET.Element | None = None,
    ) -> None:
        """Initialize vehicle from GetUserPlatforms XML element and ECM codes."""

        def _get(tag: str) -> str:
            el = veh_xml.find(f"{_NS}{tag}")
            return el.text.strip() if el is not None and el.text else ""

        self._make: str = _get("Make")
        self._model: str = _get("Model")
        self._license_plate: str = _get("Plate")
        self._platform_id: str = _get("PlatformId")
        self._address: str = _get("Address")

        lat = _get("Lat")
        lon = _get("Lon")
        self._latitude: float = float(lat) if lat else 0.0
        self._longitude: float = float(lon) if lon else 0.0

        speed = _get("Speed")
        self._speed: int = int(float(speed)) if speed else 0

        head = _get("Head")
        self._heading: int = int(float(head)) if head else 0

        mileage = _get("LastMileage")
        self._mileage: float = float(mileage) if mileage else 0.0

        voltage = _get("BatteryVoltage")
        self._battery_voltage: float = float(voltage) if voltage else 0.0

        date_str = _get("Date")
        if date_str:
            self._last_update = datetime.fromisoformat(date_str).replace(
                tzinfo=ZoneInfo("Asia/Jerusalem")
            )
        else:
            self._last_update = datetime.now(tz=ZoneInfo("Asia/Jerusalem"))

        # Engine is ON when EcmCode 31 ("engine off") is absent
        self._engine_on: bool = ECM_ENGINE_OFF not in ecm_codes
        # Locked when EcmCode 41 ("switch closed") is present
        self._locked: bool = ECM_LOCKED in ecm_codes

        # EV data from GetElectricData DiagnosticValues
        self._is_electric_vehicle: bool = False
        self._is_charging: bool = False
        self._battery_level: int | None = None
        self._battery_range: float | None = None
        self._charging_mode: str | None = None
        self._charging_time_remaining: str | None = None
        # All parsed DiagnosticValues: code -> {name, value}
        self._ev_diagnostics: dict[str, dict] = {}
        # Codes already exposed by specific typed sensors (skip in dynamic sensors)
        self._ev_covered_codes: set[str] = set()

        if electric_data_xml is not None:
            for dv in electric_data_xml.iter(f"{_NS}DiagnosticValue"):
                label_el = dv.find(f"{_NS}Label")
                value_el = dv.find(f"{_NS}Value")
                if label_el is None or value_el is None:
                    continue
                label_text = (label_el.text or "").strip()
                value_text = (value_el.text or "").strip()
                m = _LABEL_RE.match(label_text)
                if not m:
                    continue
                code = m["code"]
                self._ev_diagnostics[code] = {"name": m["name"], "value": value_text}

                if any(f in label_text for f in EV_BATTERY_LEVEL_LABELS):
                    self._battery_level = int(float(value_text)) if value_text else None
                    self._ev_covered_codes.add(code)
                elif any(f in label_text for f in EV_BATTERY_RANGE_LABELS):
                    self._battery_range = float(value_text) if value_text else None
                    self._ev_covered_codes.add(code)
                elif any(f in label_text for f in EV_CHARGING_MODE_LABELS):
                    self._charging_mode = value_text
                    self._ev_covered_codes.add(code)
                elif any(f in label_text for f in EV_CHARGING_TIME_LABELS):
                    self._charging_time_remaining = value_text
                    self._ev_covered_codes.add(code)

            self._is_electric_vehicle = (
                self._battery_level is not None or self._battery_range is not None
            )
            if self._is_electric_vehicle:
                self._is_charging = self._charging_mode not in (None, "", "0", "Off")

    @property
    def make(self) -> str:
        return self._make

    @property
    def model(self) -> str:
        return self._model

    @property
    def license_plate(self) -> str:
        return self._license_plate

    @property
    def platform_id(self) -> str:
        return self._platform_id

    @property
    def gps_coordinates(self) -> tuple[float, float]:
        return (self._latitude, self._longitude)

    @property
    def address(self) -> str:
        return self._address

    @property
    def speed(self) -> int:
        return self._speed

    @property
    def heading(self) -> int:
        return self._heading

    @property
    def mileage(self) -> float:
        return self._mileage

    @property
    def battery_voltage(self) -> float:
        return self._battery_voltage

    @property
    def last_update(self) -> datetime:
        return self._last_update

    @property
    def engine_on(self) -> bool:
        return self._engine_on

    @property
    def locked(self) -> bool:
        return self._locked

    @property
    def is_electric_vehicle(self) -> bool:
        return self._is_electric_vehicle

    @property
    def is_charging(self) -> bool:
        return self._is_charging

    @property
    def battery_level(self) -> int | None:
        return self._battery_level

    @property
    def battery_range(self) -> float | None:
        return self._battery_range

    @property
    def charging_mode(self) -> str | None:
        return self._charging_mode

    @property
    def charging_time_remaining(self) -> str | None:
        return self._charging_time_remaining

    @property
    def ev_diagnostics(self) -> dict[str, dict]:
        """All parsed DiagnosticValues by code number."""
        return self._ev_diagnostics

    @property
    def ev_covered_codes(self) -> set[str]:
        """Codes already exposed by specific typed sensors."""
        return self._ev_covered_codes

    def __str__(self) -> str:
        return f"{self._make} {self._model} ({self._license_plate})"
