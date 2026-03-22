import asyncio
import logging

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN, RECONNECT_DELAY
from .udp_commands import amp_channel_off, amp_channel_on, cancel_and_replace

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity_key, data in hass.data[DOMAIN].items():
        conf = data["config"]
        state = data["state"]
        entities.append(C4ZoneMediaPlayer(entity_key, conf, state, data))
    async_add_entities(entities)


class C4ZoneMediaPlayer(MediaPlayerEntity, RestoreEntity):
    _attr_should_poll = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, entity_key, config, state, data):
        self._entity_key = entity_key
        self._attr_name = config["name"]
        self._channel = config["channel"]
        self._ip = config["ip"]
        self._port = config["port"]
        self._sources_map = config.get("sources", {})  # id -> name
        self._state_ref = state
        self._data = data
        self._attr_available = True
        self._attr_unique_id = f"c4_amp_{self._ip}_ch{self._channel}_player"
        self._attr_source_list = list(self._sources_map.values())
        self._reconnect_task: asyncio.Task | None = None

        self._state_ref.setdefault("power", False)
        self._state_ref.setdefault("source", None)

    @property
    def state(self):
        return STATE_ON if self._state_ref.get("power") else STATE_OFF

    @property
    def source(self):
        return self._state_ref.get("source")

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

    async def async_will_remove_from_hass(self):
        if self._reconnect_task:
            self._reconnect_task.cancel()

    @callback
    def _handle_result(self, success: bool) -> None:
        if success:
            if not self._attr_available:
                self._attr_available = True
                self.async_write_ha_state()
        else:
            self._attr_available = False
            self.async_write_ha_state()
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = self.hass.async_create_task(self._reconnect())

    async def _ping(self) -> bool | None:
        cancel = cancel_and_replace(self._data)
        source = self._state_ref.get("source")
        source_id = self._get_source_id(source) if source else None
        if self._state_ref.get("power") and source_id:
            return await amp_channel_on(self._channel, source_id, self._ip, self._port, cancel=cancel)
        return await amp_channel_off(self._channel, self._ip, self._port, cancel=cancel)

    async def _reconnect(self) -> None:
        try:
            while not self._attr_available:
                await asyncio.sleep(RECONNECT_DELAY)
                result = await self._ping()
                if result is None:
                    return
                self._handle_result(result)
        except asyncio.CancelledError:
            pass

    async def async_turn_on(self):
        source = self._attr_source_list[0] if self._attr_source_list else None
        if not source:
            return

        source_id = self._get_source_id(source)
        if source_id is None:
            return

        cancel = cancel_and_replace(self._data)
        result = await amp_channel_on(self._channel, source_id, self._ip, self._port, cancel=cancel)
        if result is None:
            return
        self._handle_result(result)
        if result:
            self._state_ref["power"] = True
            self._state_ref["source"] = source
            self.async_write_ha_state()

    async def async_turn_off(self):
        cancel = cancel_and_replace(self._data)
        result = await amp_channel_off(self._channel, self._ip, self._port, cancel=cancel)
        if result is None:
            return
        self._handle_result(result)
        if result:
            self._state_ref["power"] = False
            self._state_ref["source"] = None
            self.async_write_ha_state()

    async def async_select_source(self, source):
        if source not in self._attr_source_list:
            return

        source_id = self._get_source_id(source)
        if source_id is None:
            _LOGGER.warning("Unknown source '%s' for %s", source, self._attr_name)
            return

        cancel = cancel_and_replace(self._data)
        result = await amp_channel_on(self._channel, source_id, self._ip, self._port, cancel=cancel)
        if result is None:
            return
        self._handle_result(result)
        if result:
            self._state_ref["power"] = True
            self._state_ref["source"] = source
            self.async_write_ha_state()

    def _get_source_id(self, source: str) -> int | None:
        for k, v in self._sources_map.items():
            if v == source:
                return int(k)
        return None
