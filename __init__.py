import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "c4_amp"

ZONE_SCHEMA = vol.Schema({
    vol.Required("ip"): cv.string,
    vol.Required("channel"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
    vol.Optional("port"): cv.port,  # accepted for backwards compat, ignored (hardcoded to 8750)
    vol.Optional("sources", default={}): {vol.Coerce(int): cv.string},
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: {cv.string: ZONE_SCHEMA},
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up via YAML."""
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})

    for name, zone_conf in config[DOMAIN].items():
        channel = zone_conf["channel"]
        ip = zone_conf["ip"]
        sources = zone_conf.get("sources", {})

        entity_key = f"{ip}_{channel}"

        # Defaults only. Each entity uses RestoreEntity to overwrite these
        # from the last HA-known state.
        hass.data[DOMAIN][entity_key] = {
            "config": {
                "name": name,
                "channel": channel,
                "ip": ip,
                "sources": sources,
            },
            "state": {
                "power": False,
                "volume": 0.5,
                "source": None,
            },
        }

    await async_load_platform(hass, "media_player", DOMAIN, {}, config)
    await async_load_platform(hass, "switch", DOMAIN, {}, config)
    await async_load_platform(hass, "number", DOMAIN, {}, config)
    await async_load_platform(hass, "select", DOMAIN, {}, config)

    return True
