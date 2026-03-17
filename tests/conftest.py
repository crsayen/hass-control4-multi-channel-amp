import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure repo root is on sys.path so `custom_components` is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Minimal stubs for homeassistant modules.
# These must be registered before any of our integration code is imported.
# Each entity base class must be a distinct class — Python 3.12+ forbids
# duplicate bases (e.g. both SwitchEntity and RestoreEntity mapping to object).
# ---------------------------------------------------------------------------

def _callback(func):
    """Stub: @callback is a no-op in tests."""
    return func


class _FakeMediaPlayerFeatures:
    TURN_ON = 1
    TURN_OFF = 2
    SELECT_SOURCE = 4


class _RestoreEntity:
    pass


class _SwitchEntity:
    pass


class _NumberEntity:
    pass


class _SelectEntity:
    pass


class _MediaPlayerEntity:
    pass


_ha_core = MagicMock()
_ha_core.callback = _callback

_ha_const = MagicMock()
_ha_const.STATE_ON = "on"
_ha_const.STATE_OFF = "off"

_ha_cv = MagicMock()
_ha_cv.string = str
_ha_cv.port = int

_ha_restore = MagicMock()
_ha_restore.RestoreEntity = _RestoreEntity

_ha_switch = MagicMock()
_ha_switch.SwitchEntity = _SwitchEntity

_ha_number = MagicMock()
_ha_number.NumberEntity = _NumberEntity

_ha_select = MagicMock()
_ha_select.SelectEntity = _SelectEntity

_ha_media_player = MagicMock()
_ha_media_player.MediaPlayerEntity = _MediaPlayerEntity
_ha_media_player.MediaPlayerEntityFeature = _FakeMediaPlayerFeatures

# `from homeassistant.helpers import config_validation as cv` resolves
# `.config_validation` as an attribute of the helpers module object, so we
# must set it explicitly rather than relying on sys.modules alone.
_ha_helpers = MagicMock()
_ha_helpers.config_validation = _ha_cv
_ha_helpers.restore_state = _ha_restore
_ha_helpers.discovery = MagicMock()
_ha_helpers.typing = MagicMock()

sys.modules.update({
    "homeassistant": MagicMock(),
    "homeassistant.core": _ha_core,
    "homeassistant.const": _ha_const,
    "homeassistant.components": MagicMock(),
    "homeassistant.components.switch": _ha_switch,
    "homeassistant.components.number": _ha_number,
    "homeassistant.components.select": _ha_select,
    "homeassistant.components.media_player": _ha_media_player,
    "homeassistant.helpers": _ha_helpers,
    "homeassistant.helpers.restore_state": _ha_restore,
    "homeassistant.helpers.config_validation": _ha_cv,
    "homeassistant.helpers.discovery": _ha_helpers.discovery,
    "homeassistant.helpers.typing": _ha_helpers.typing,
})
