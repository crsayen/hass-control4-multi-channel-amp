import logging

from homeassistant.components.number import NumberEntity

from . import DOMAIN
from .udp_commands import amp_channel_volume

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity_key, data in hass.data[DOMAIN].items():
        conf = data["config"]
        state = data["state"]
        entities.append(C4ZoneVolumeSlider(hass, entity_key, conf, state))
    async_add_entities(entities)

class C4ZoneVolumeSlider(NumberEntity):
    def __init__(self, hass, entity_key, config, state):
        self.hass = hass
        self._entity_key = entity_key
        self._name = f"{config['name']} Volume"
        self._channel = config["channel"]
        self._ip = config["ip"]
        self._state_ref = state

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._state_ref["volume"]

    @property
    def native_min_value(self):
        return 0.0

    @property
    def native_max_value(self):
        return 1.0

    @property
    def native_step(self):
        return 0.01

    async def async_set_native_value(self, value: float) -> None:
        amp_channel_volume(self._channel, value, self._ip)
        self._state_ref["volume"] = value
        self.async_write_ha_state()
