import asyncio
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .udp_commands import amp_channel_volume

_LOGGER = logging.getLogger(__name__)

DEBOUNCE_DELAY = 0.3  # seconds


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for entity_key, data in hass.data[DOMAIN].items():
        conf = data["config"]
        state = data["state"]
        entities.append(C4ZoneVolumeSlider(hass, entity_key, conf, state))
    async_add_entities(entities)


class C4ZoneVolumeSlider(NumberEntity, RestoreEntity):
    def __init__(self, hass, entity_key, config, state):
        self.hass = hass
        self._entity_key = entity_key
        self._name = f"{config['name']} Volume"
        self._channel = config["channel"]
        self._ip = config["ip"]
        self._port = config["port"]
        self._state_ref = state
        self._debounce_task: asyncio.Task | None = None

        self._state_ref.setdefault("volume", 0.5)

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self):
        return f"c4_amp_{self._ip}_ch{self._channel}_volume"

    @property
    def native_value(self):
        return float(self._state_ref.get("volume", 0.0))

    @property
    def native_min_value(self):
        return 0.0

    @property
    def native_max_value(self):
        return 1.0

    @property
    def native_step(self):
        return 0.01

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        try:
            self._state_ref["volume"] = float(last_state.state)
        except (ValueError, TypeError):
            _LOGGER.debug("Could not restore volume state: %s", last_state.state)
            return

        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        if self._debounce_task:
            self._debounce_task.cancel()

    async def async_set_native_value(self, value: float) -> None:
        value = max(self.native_min_value, min(self.native_max_value, float(value)))

        # Update state immediately so the UI stays responsive while dragging.
        self._state_ref["volume"] = value
        self.async_write_ha_state()

        # Cancel any pending send and reschedule.
        if self._debounce_task:
            self._debounce_task.cancel()
        self._debounce_task = self.hass.async_create_task(self._send_volume(value))

    async def _send_volume(self, value: float) -> None:
        try:
            await asyncio.sleep(DEBOUNCE_DELAY)
            if not await amp_channel_volume(self._channel, value, self._ip, self._port):
                # Command failed — revert the optimistic state update.
                self._state_ref["volume"] = value
                self.async_write_ha_state()
        except asyncio.CancelledError:
            pass
