import logging
from homeassistant import config_entries
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.components.switch import SwitchEntity, DEVICE_CLASS_SWITCH

from . import SleepIQDataUpdateCoordinator, SleepIQDevice
from .const import ATTRIBUTION_TEXT, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass, config_entry: config_entries.ConfigEntry, async_add_entities
):
    """Set up a bed from a config entry."""
    coordinator: SleepIQDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    switches = []
    # if coordinator.data.light1 is not None:
    switches.append(ResponsiveAirSwitch(coordinator, "left"))
    switches.append(ResponsiveAirSwitch(coordinator, "right"))
    switches.append(PrivacyModeSwitch(coordinator))

    async_add_entities(switches)


class PrivacyModeSwitch(SleepIQDevice, SwitchEntity):
    """Representation of a SleepIQ responsive air switch."""

    def __init__(self, coordinator: SleepIQDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._unique_id = DOMAIN + "_" + self._coordinator.data.bedId + "_privacy_mode"
        self._name = "Sleep Number privacy mode"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return {
            "accountId": self._coordinator.data.privacy_mode.accountId,
            "bedId": self._coordinator.data.privacy_mode.bedId,
            "pauseMode": self._coordinator.data.privacy_mode.pauseMode,
            ATTR_ATTRIBUTION: ATTRIBUTION_TEXT,
        }

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return DEVICE_CLASS_SWITCH

    async def async_turn_on(self):
        """Send the on command."""
        _LOGGER.debug("Turning on privacy mode")
        self._coordinator.data.privacy_mode.pauseMode = "on"
        await self._coordinator.sleepiq.turn_on_privacy_mode()

    async def async_turn_off(self, **kwargs):
        """Send the off command."""
        _LOGGER.debug("Turning off privacy mode")
        self._coordinator.data.privacy_mode.pauseMode = "off"
        await self._coordinator.sleepiq.turn_off_privacy_mode()

    @property
    def is_on(self):
        """Get whether the switch is in on state."""
        if self._coordinator.data.privacy_mode.pauseMode == "off":
            return False
        elif self._coordinator.data.privacy_mode.pauseMode == "on":
            return True


class ResponsiveAirSwitch(SleepIQDevice, SwitchEntity):
    """Representation of a SleepIQ responsive air switch."""

    def __init__(self, coordinator: SleepIQDataUpdateCoordinator, side):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._side = side
        self._unique_id = (
            DOMAIN
            + "_"
            + self._coordinator.data.bedId
            + "_"
            + self._side
            + "responsive_air"
        )

        if self._side.lower() == "left":
            self._name = (
                self._coordinator.data.left_side.sleeper.firstName + " responsive air"
            )
        elif self._side.lower() == "right":
            self._name = (
                self._coordinator.data.right_side.sleeper.firstName + " responsive air"
            )

    @property
    def name(self):
        """Return the name of the sensor."""

        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return {
            "adjustmentThreshold": self._coordinator.data.responsive_air.adjustmentThreshold,
            "inBedTimeout": self._coordinator.data.responsive_air.inBedTimeout,
            "leftSideEnabled": self._coordinator.data.responsive_air.leftSideEnabled,
            "outOfBedTimeout": self._coordinator.data.responsive_air.outOfBedTimeout,
            "pollFrequency": self._coordinator.data.responsive_air.pollFrequency,
            "prefSyncState": self._coordinator.data.responsive_air.prefSyncState,
            "rightSideEnabled": self._coordinator.data.responsive_air.rightSideEnabled,
            ATTR_ATTRIBUTION: ATTRIBUTION_TEXT,
        }

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return DEVICE_CLASS_SWITCH

    async def async_turn_on(self, **kwargs):
        """Send the on command."""
        _LOGGER.debug("Turning on %s", self._name)

        if self._side.lower() == "left":
            self._coordinator.data.responsive_air.leftSideEnabled = True
        elif self._side.lower() == "right":
            self._coordinator.data.responsive_air.leftSideEnabled = True

        await self._coordinator.sleepiq.turn_on_responsive_air(self._side)

    async def async_turn_off(self, **kwargs):
        """Send the off command."""
        _LOGGER.debug("Turning off %s", self._name)
        if self._side.lower() == "left":
            self._coordinator.data.responsive_air.leftSideEnabled = False
        elif self._side.lower() == "right":
            self._coordinator.data.responsive_air.leftSideEnabled = False
        await self._coordinator.sleepiq.turn_off_responsive_air(self._side)
        # await self.tesla_device.stop_charge()
        # self.async_write_ha_state()

    @property
    def is_on(self):
        """Get whether the switch is in on state."""
        if self._side.lower() == "left":
            return self._coordinator.data.responsive_air.leftSideEnabled
        elif self._side.lower() == "right":
            return self._coordinator.data.responsive_air.rightSideEnabled
        else:
            return None
        # if self.tesla_device.is_charging() is None:
        #     return None
        # return self.tesla_device.is_charging()