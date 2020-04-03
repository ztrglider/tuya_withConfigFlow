"""Support for Tuya Smart devices."""
from datetime import timedelta
import logging

from tuyaha import TuyaApi
import voluptuous as vol

from homeassistant.const import CONF_PASSWORD, CONF_PLATFORM, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval

from .const import TUYA_DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_COUNTRYCODE = "country_code"

DOMAIN = "tuya"
DATA_TUYA = "data_tuya"

SIGNAL_DELETE_ENTITY = "tuya_delete"
SIGNAL_UPDATE_ENTITY = "tuya_update"

SERVICE_FORCE_UPDATE = "force_update"
SERVICE_PULL_DEVICES = "pull_devices"

TUYA_TYPE_TO_HA = {
    "climate": "climate",
    "cover": "cover",
    "fan": "fan",
    "light": "light",
    "scene": "scene",
    "switch": "switch",
}

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_COUNTRYCODE): cv.string,
                vol.Optional(CONF_PLATFORM, default="tuya"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up Tuya Component."""

    if DOMAIN not in config:
        # There is an entry and nothing in configuration.yaml
        _LOGGER.info("no Tuya config in configuration.yaml")
        return True

    tuya = TuyaApi()
    username = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]
    country_code = config[DOMAIN][CONF_COUNTRYCODE]
    platform = config[DOMAIN][CONF_PLATFORM]

    hass.data[DATA_TUYA] = tuya
    tuya.init(username, password, country_code, platform)
    hass.data[DOMAIN] = {"entities": {}}

    def load_devices(device_list):
        """Load new devices by device_list."""
        device_type_list = {}
        for device in device_list:
            dev_type = device.device_type()
            if (
                    dev_type in TUYA_TYPE_TO_HA
                    and device.object_id() not in hass.data[DOMAIN]["entities"]
            ):
                ha_type = TUYA_TYPE_TO_HA[dev_type]
                if ha_type not in device_type_list:
                    device_type_list[ha_type] = []
                device_type_list[ha_type].append(device.object_id())
                hass.data[DOMAIN]["entities"][device.object_id()] = None
        for ha_type, dev_ids in device_type_list.items():
            discovery.load_platform(hass, ha_type, DOMAIN, {"dev_ids": dev_ids}, config)

    device_list = tuya.get_all_devices()
    load_devices(device_list)

    def poll_devices_update(event_time):
        """Check if accesstoken is expired and pull device list from server."""
        _LOGGER.debug("Pull devices from Tuya.")
        tuya.poll_devices_update()
        # Add new discover device.
        device_list = tuya.get_all_devices()
        load_devices(device_list)
        # Delete not exist device.
        newlist_ids = []
        for device in device_list:
            newlist_ids.append(device.object_id())
        for dev_id in list(hass.data[DOMAIN]["entities"]):
            if dev_id not in newlist_ids:
                dispatcher_send(hass, SIGNAL_DELETE_ENTITY, dev_id)
                hass.data[DOMAIN]["entities"].pop(dev_id)

    track_time_interval(hass, poll_devices_update, timedelta(minutes=5))

    hass.services.register(DOMAIN, SERVICE_PULL_DEVICES, poll_devices_update)

    def force_update(call):
        """Force all devices to pull data."""
        dispatcher_send(hass, SIGNAL_UPDATE_ENTITY)

    hass.services.register(DOMAIN, SERVICE_FORCE_UPDATE, force_update)

    return True


async def async_setup_entry(hass, entry):
    """Set up config entry"""

    tuya = TuyaApi()

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    country_code = entry.data[CONF_COUNTRYCODE]
    platform = entry.data[CONF_PLATFORM]

    hass.data[DATA_TUYA] = tuya
    tuya.init(username, password, country_code, platform)

    hass.data[DOMAIN] = {"entities": {}}

    for component in ("climate", "cover", "fan", "light", "switch"):
        hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, component))

    # def load_devices(device_list):
    #     """Load new devices by device_list."""
    #     device_type_list = {}
    #     for device in device_list:
    #         dev_type = device.device_type()
    #         if (
    #                 dev_type in TUYA_TYPE_TO_HA
    #                 and device.object_id() not in hass.data[DOMAIN]["entities"]
    #         ):
    #             ha_type = TUYA_TYPE_TO_HA[dev_type]
    #             if ha_type not in device_type_list:
    #                 device_type_list[ha_type] = []
    #             device_type_list[ha_type].append(device.object_id())
    #             hass.data[DOMAIN]["entities"][device.object_id()] = None
    #     for ha_type, dev_ids in device_type_list.items():
    #         discovery.load_platform(hass, ha_type, DOMAIN, {"dev_ids": dev_ids}, entry.data)
    #
    # _LOGGER.info("debug4")
    #
    # device_list = tuya.get_all_devices()
    # #load_devices(device_list)

    # def poll_devices_update(event_time):
    #     """Check if accesstoken is expired and pull device list from server."""
    #     _LOGGER.debug("Pull devices from Tuya.")
    #     tuya.poll_devices_update()
    #     # Add new discover device.
    #     device_list = tuya.get_all_devices()
    #     load_devices(device_list)
    #     # Delete not exist device.
    #     newlist_ids = []
    #     for device in device_list:
    #         newlist_ids.append(device.object_id())
    #     for dev_id in list(hass.data[DOMAIN]["entities"]):
    #         if dev_id not in newlist_ids:
    #             dispatcher_send(hass, SIGNAL_DELETE_ENTITY, dev_id)
    #             hass.data[DOMAIN]["entities"].pop(dev_id)
    #
    # _LOGGER.info("debug5")
    #
    # # track_time_interval(hass, poll_devices_update, timedelta(minutes=5))
    # _LOGGER.info("debug5.5")
    #
    # hass.services.register(DOMAIN, SERVICE_PULL_DEVICES, poll_devices_update)

    # _LOGGER.info("debug6")
    #     #
    #     # def force_update(call):
    #     #     """Force all devices to pull data."""
    #     #     dispatcher_send(hass, SIGNAL_UPDATE_ENTITY)
    #     #
    #     # _LOGGER.info("debug6.5")
    #     #
    #     # hass.services.register(DOMAIN, SERVICE_FORCE_UPDATE, force_update)
    #     #
    #     # _LOGGER.info("debug7")

    return True


async def async_unload_entry(hass, entry):
    _ = hass.data[DOMAIN].pop
    # Unloaded not yet configured restart required to unload integration
    return False



def get_all_devices_of_type(hass, type):
    """Set up Tuya Switch platform."""
    tuya = hass.data[DATA_TUYA]

    device_ids = []
    for device in tuya.get_all_devices():
        if device.device_type() == type:
            device_ids.append(device.object_id())

    devices = []
    for device_id in device_ids:
        device = tuya.get_device_by_id(device_id)
        if device is None:
            continue
        devices.append(device)
    return devices


class TuyaDevice(Entity):
    """Tuya base device."""

    def __init__(self, tuya):
        """Init Tuya devices."""
        self.tuya = tuya

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        dev_id = self.tuya.object_id()
        self.hass.data[DOMAIN]["entities"][dev_id] = self.entity_id
        async_dispatcher_connect(self.hass, SIGNAL_DELETE_ENTITY, self._delete_callback)
        async_dispatcher_connect(self.hass, SIGNAL_UPDATE_ENTITY, self._update_callback)

    @property
    def object_id(self):
        """Return Tuya device id."""
        return self.tuya.object_id()

    @property
    def unique_id(self):
        """Return a unique ID."""
        return "tuya.{}".format(self.tuya.object_id())

    @property
    def name(self):
        """Return Tuya device name."""
        return self.tuya.name()

    @property
    def available(self):
        """Return if the device is available."""
        return self.tuya.available()

    def update(self):
        """Refresh Tuya device data."""
        self.tuya.update()

    @callback
    def _delete_callback(self, dev_id):
        """Remove this entity."""
        if dev_id == self.object_id:
            self.hass.async_create_task(self.async_remove())

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id.split('_')[0])},
            "name": self.name,
            "manufacturer": "tuya_manufacturer",
            "model": "tuya_model",
            "sw_version": "1.0",
            "via_device": (DOMAIN, "tuya_dummy_bridge"),
        }
