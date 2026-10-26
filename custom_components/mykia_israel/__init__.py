"""The Kia Ituran integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import KiaIturanConfigEntry, KiaIturanDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: KiaIturanConfigEntry) -> None:
    """Set up Kia Ituran from a config entry."""
    coordinator = KiaIturanDataUpdateCoordinator(hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(hass: HomeAssistant, entry: KiaIturanConfigEntry) -> None:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
