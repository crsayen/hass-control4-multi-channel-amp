import logging

from homeassistant.components.switch import SwitchEntity

from . import DOMAIN
from .udp_commands import amp_channel_on, amp_channel_off

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity_key, data in hass.data[DOMAIN].items():
        conf = data["config"]
        state = data["state"]
        entities.append(C4ZonePowerSwitch(hass, entity_key, conf, state))
    async_add_entities(entities)

class C4ZonePowerSwitch(SwitchEntity):
    def __init__(self, hass, entity_key, config, state):
        self.hass = hass
        self._entity_key = entity_key
        self._name = f"{config['name']} Power"
        self._channel = config["channel"]
        self._ip = config["ip"]
        self._sources = config.get("sources", {})
        self._state_ref = state

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state_ref["power"]

    async def async_turn_on(self, **kwargs):
        if self._sources:
            first_source = list(self._sources.keys())[0]
            amp_channel_on(self._channel, int(first_source), self._ip)
            self._state_ref["power"] = True
            self._state_ref["source"] = self._sources[first_source]
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        amp_channel_off(self._channel, self._ip)
        self._state_ref["power"] = False
        self._state_ref["source"] = None
        self.async_write_ha_state()
