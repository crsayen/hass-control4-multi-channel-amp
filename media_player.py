import logging

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.components.media_player.const import MediaPlayerState
from homeassistant.const import STATE_OFF, STATE_ON

from . import DOMAIN
from .udp_commands import amp_channel_on, amp_channel_off

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity_key, data in hass.data[DOMAIN].items():
        conf = data["config"]
        state = data["state"]
        entities.append(C4ZoneMediaPlayer(hass, entity_key, conf, state))
    async_add_entities(entities, update_before_add=True)

class C4ZoneMediaPlayer(MediaPlayerEntity):
    def __init__(self, hass, entity_key, config, state):
        self.hass = hass
        self._entity_key = entity_key
        self._name = config["name"]
        self._channel = config["channel"]
        self._ip = config["ip"]
        self._sources = list(config.get("sources", {}).values())
        self._state_ref = state

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return STATE_ON if self._state_ref["power"] else STATE_OFF

    @property
    def source(self):
        return self._state_ref["source"]

    @property
    def source_list(self):
        return self._sources

    @property
    def supported_features(self):
        return MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF | MediaPlayerEntityFeature.SELECT_SOURCE

    async def async_turn_on(self):
        source = self._sources[0] if self._sources else None
        if source:
            source_id = self._get_source_id(source)
            amp_channel_on(self._channel, source_id, self._ip)
            self._state_ref["power"] = True
            self._state_ref["source"] = source
            self.async_write_ha_state()

    async def async_turn_off(self):
        amp_channel_off(self._channel, self._ip)
        self._state_ref["power"] = False
        self._state_ref["source"] = None
        self.async_write_ha_state()

    async def async_select_source(self, source):
        if source in self._sources:
            source_id = self._get_source_id(source)
            amp_channel_on(self._channel, source_id, self._ip)
            self._state_ref["power"] = True
            self._state_ref["source"] = source
            self.async_write_ha_state()

    def _get_source_id(self, source):
        for k, v in self.hass.data[DOMAIN][self._entity_key]["config"]["sources"].items():
            if v == source:
                return int(k)
        return 1
