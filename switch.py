import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .udp_commands import amp_channel_off, amp_channel_on

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity_key, data in hass.data[DOMAIN].items():
        conf = data["config"]
        state = data["state"]
        entities.append(C4ZonePowerSwitch(hass, entity_key, conf, state))
    async_add_entities(entities)


class C4ZonePowerSwitch(SwitchEntity, RestoreEntity):
    def __init__(self, hass, entity_key, config, state):
        self.hass = hass
        self._entity_key = entity_key
        self._name = f"{config['name']} Power"
        self._channel = config["channel"]
        self._ip = config["ip"]
        self._port = config["port"]
        self._sources = config.get("sources", {})
        self._state_ref = state

        self._state_ref.setdefault("power", False)
        self._state_ref.setdefault("source", None)

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self):
        return f"c4_amp_{self._ip}_ch{self._channel}_power"

    @property
    def is_on(self):
        return bool(self._state_ref.get("power", False))

    @property
    def extra_state_attributes(self):
        # Persist + restore "source" too
        return {
            "source": self._state_ref.get("source"),
            "channel": self._channel,
            "ip": self._ip,
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        self._state_ref["power"] = (last_state.state == "on")
        if last_state.attributes:
            self._state_ref["source"] = last_state.attributes.get("source")

        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        if self._sources:
            first_source_id = list(self._sources.keys())[0]
            if await amp_channel_on(self._channel, int(first_source_id), self._ip, self._port):
                self._state_ref["power"] = True
                self._state_ref["source"] = self._sources[first_source_id]
                self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if await amp_channel_off(self._channel, self._ip, self._port):
            self._state_ref["power"] = False
            self._state_ref["source"] = None
            self.async_write_ha_state()