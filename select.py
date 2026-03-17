import asyncio
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .udp_commands import amp_channel_off, amp_channel_on

_LOGGER = logging.getLogger(__name__)

RECONNECT_DELAY = 30  # seconds


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity_key, data in hass.data[DOMAIN].items():
        conf = data["config"]
        state = data["state"]
        if conf.get("sources"):
            entities.append(C4ZoneSourceSelect(entity_key, conf, state))
    async_add_entities(entities)


class C4ZoneSourceSelect(SelectEntity, RestoreEntity):
    def __init__(self, entity_key, config, state):
        self._entity_key = entity_key
        self._name = f"{config['name']} Source"
        self._channel = config["channel"]
        self._ip = config["ip"]
        self._port = config["port"]
        self._sources_map = config.get("sources", {})  # id -> name
        self._state_ref = state
        self._available = True
        self._reconnect_task: asyncio.Task | None = None

        self._state_ref.setdefault("source", None)

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self):
        return f"c4_amp_{self._ip}_ch{self._channel}_source"

    @property
    def available(self) -> bool:
        return self._available

    @property
    def options(self) -> list[str]:
        return list(self._sources_map.values())

    @property
    def current_option(self) -> str | None:
        return self._state_ref.get("source")

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        if last_state.state in self.options:
            self._state_ref["source"] = last_state.state

        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        if self._reconnect_task:
            self._reconnect_task.cancel()

    def _handle_result(self, success: bool) -> None:
        if success:
            if not self._available:
                self._available = True
                self.async_write_ha_state()
        else:
            self._available = False
            self.async_write_ha_state()
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = self.hass.async_create_task(self._reconnect())

    async def _ping(self) -> bool:
        source = self._state_ref.get("source")
        source_id = self._get_source_id(source) if source else None
        if source_id and self._state_ref.get("power"):
            return await amp_channel_on(self._channel, source_id, self._ip, self._port)
        return await amp_channel_off(self._channel, self._ip, self._port)

    async def _reconnect(self) -> None:
        try:
            while not self._available:
                await asyncio.sleep(RECONNECT_DELAY)
                self._handle_result(await self._ping())
        except asyncio.CancelledError:
            pass

    async def async_select_option(self, option: str) -> None:
        source_id = self._get_source_id(option)
        if source_id is None:
            _LOGGER.warning("Unknown source '%s' for %s", option, self._name)
            return

        success = await amp_channel_on(self._channel, source_id, self._ip, self._port)
        self._handle_result(success)
        if success:
            self._state_ref["power"] = True
            self._state_ref["source"] = option
            self.async_write_ha_state()

    def _get_source_id(self, source: str) -> int | None:
        for k, v in self._sources_map.items():
            if v == source:
                return int(k)
        return None
