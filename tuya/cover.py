"""Support for Tuya covers."""
from homeassistant.components.cover import (
    ENTITY_ID_FORMAT,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_STOP,
    CoverDevice,
)

from . import DATA_TUYA, TuyaDevice, get_all_devices_of_type


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Tuya cover devices."""
    if discovery_info is None:
        return
    tuya = hass.data[DATA_TUYA]
    dev_ids = discovery_info.get("dev_ids")
    devices = []
    for dev_id in dev_ids:
        device = tuya.get_device_by_id(dev_id)
        if device is None:
            continue
        devices.append(TuyaCover(device))
    add_entities(devices)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up Tuya Switch platform."""

    devices = []
    for device in get_all_devices_of_type(hass, "cover"):
        devices.append(TuyaCover(device))

    async_add_devices(devices)


class TuyaCover(TuyaDevice, CoverDevice):
    """Tuya cover devices."""

    def __init__(self, tuya):
        """Init tuya cover device."""
        super().__init__(tuya)
        self.entity_id = ENTITY_ID_FORMAT.format(tuya.object_id())

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = SUPPORT_OPEN | SUPPORT_CLOSE
        if self.tuya.support_stop():
            supported_features |= SUPPORT_STOP
        return supported_features

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        state = self.tuya.state()
        if state == 1:
            return False
        if state == 2:
            return True
        return None

    def open_cover(self, **kwargs):
        """Open the cover."""
        self.tuya.open_cover()

    def close_cover(self, **kwargs):
        """Close cover."""
        self.tuya.close_cover()

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self.tuya.stop_cover()
