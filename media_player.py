import logging

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .udp_commands import amp_channel_off, amp_channel_on

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity_key, data in hass.data[DOMAIN].items():
        conf = data["config"]
        state = data["state"]
        entities.append(C4ZoneMediaPlayer(hass, entity_key, conf, state))
    async_add_entities(entities)


class C4ZoneMediaPlayer(MediaPlayerEntity, RestoreEntity):
    def __init__(self, hass, entity_key, config, state):
        self.hass = hass
        self._entity_key = entity_key
        self._name = config["name"]
        self._channel = config["channel"]
        self._ip = config["ip"]
        self._sources_map = config.get("sources", {})  # id -> name
        self._sources = list(self._sources_map.values())
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
        return f"c4_amp_{self._ip}_ch{self._channel}_player"

    @property
    def state(self):
        return STATE_ON if self._state_ref.get("power") else STATE_OFF

    @property
    def source(self):
        return self._state_ref.get("source")

    @property
    def source_list(self):
        return self._sources

    @property
    def supported_features(self):
        return (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )

    @property
    def extra_state_attributes(self):
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

        self._state_ref["power"] = (last_state.state == STATE_ON)
        if last_state.attributes:
            self._state_ref["source"] = last_state.attributes.get("source")

        self.async_write_ha_state()

    async def async_turn_on(self):
        source = self._sources[0] if self._sources else None
        if not source:
            return

        source_id = self._get_source_id(source)
        if source_id is None:
            return

        if await amp_channel_on(self._channel, source_id, self._ip):
            self._state_ref["power"] = True
            self._state_ref["source"] = source
            self.async_write_ha_state()

    async def async_turn_off(self):
        if await amp_channel_off(self._channel, self._ip):
            self._state_ref["power"] = False
            self._state_ref["source"] = None
            self.async_write_ha_state()

    async def async_select_source(self, source):
        if source not in self._sources:
            return

        source_id = self._get_source_id(source)
        if source_id is None:
            _LOGGER.warning("Unknown source '%s' for %s", source, self._name)
            return

        if await amp_channel_on(self._channel, source_id, self._ip):
            self._state_ref["power"] = True
            self._state_ref["source"] = source
            self.async_write_ha_state()

    def _get_source_id(self, source: str) -> int | None:
        for k, v in self._sources_map.items():
            if v == source:
                return int(k)
        return None
