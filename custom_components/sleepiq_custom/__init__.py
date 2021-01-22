"""The SleepIQ Custom integration."""
import asyncio
import logging
from typing import Any, Dict

from sleepi.models import Bed
from sleepi.sleepiq import SleepIQ

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DEVICE_MANUFACTURER,
    DEVICE_NAME,
    DEVICE_SW_VERSION,
    DOMAIN,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["light", "sensor", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the SleepIQ Custom component."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up SleepIQ Custom from a config entry."""

    coordinator = SleepIQDataUpdateCoordinator(hass, config_entry=config_entry)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    username = entry.title
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Unloaded entry for %s", username)

    return unload_ok


class SleepIQDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching SleepIQ data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize global SleepIQ data updater."""

        config = config_entry.data
        username = config["username"]
        password = config["password"]
        websession = async_get_clientsession(hass)
        self.sleepiq = SleepIQ(username, password, websession)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    def update_listeners(self) -> None:
        """Call update on all listeners."""
        for update_callback in self._listeners:
            update_callback()

    async def _async_update_data(self) -> Bed:
        """Fetch data from API endpoint."""
        try:
            _LOGGER.debug("Fetching data")
            await self.sleepiq.login()
            return await self.sleepiq.fetch_homeassistant_data()
        except Exception as e:
            message = "SleepIQ failed to login, double check your username and password"
            _LOGGER.error(message)
            _LOGGER.error(e)


class SleepIQDevice(CoordinatorEntity):
    def __init__(
        self,
        coordinator: SleepIQDataUpdateCoordinator,
    ):
        """Initialize the SleepIQ entity."""
        self._coordinator = coordinator
        super().__init__(coordinator)

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about this Sleep IQ device."""
        return {
            "identifiers": {(DOMAIN, "sleepiq-device")},
            "name": DEVICE_NAME,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": self._coordinator.data.model,
            "sw_version": DEVICE_SW_VERSION,
        }
