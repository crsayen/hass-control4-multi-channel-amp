"""Tests for entity state and availability logic."""
from unittest.mock import AsyncMock, MagicMock

from custom_components.c4_amp.media_player import C4ZoneMediaPlayer
from custom_components.c4_amp.number import C4ZoneVolumeSlider
from custom_components.c4_amp.select import C4ZoneSourceSelect
from custom_components.c4_amp.switch import C4ZonePowerSwitch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_config(**overrides):
    cfg = {
        "name": "Test Zone",
        "channel": 1,
        "ip": "192.168.1.100",
        "port": 8750,
        "sources": {1: "WiiM", 2: "TV"},
    }
    cfg.update(overrides)
    return cfg


def _mock_hass():
    hass = MagicMock()
    task = MagicMock()
    task.done.return_value = False
    hass.async_create_task.return_value = task
    return hass


def _attach_mocks(entity):
    entity.hass = _mock_hass()
    entity.async_write_ha_state = MagicMock()
    # Stub _reconnect so _handle_result doesn't create an unawaited coroutine.
    entity._reconnect = AsyncMock()
    return entity


def _make_switch(**overrides):
    return _attach_mocks(C4ZonePowerSwitch("key", _base_config(**overrides), {}))


def _make_slider(**overrides):
    return _attach_mocks(C4ZoneVolumeSlider("key", _base_config(**overrides), {}))


def _make_select(**overrides):
    return _attach_mocks(C4ZoneSourceSelect("key", _base_config(**overrides), {}))


def _make_player(**overrides):
    return _attach_mocks(C4ZoneMediaPlayer("key", _base_config(**overrides), {}))


# ---------------------------------------------------------------------------
# _handle_result — tested on switch; pattern is identical across all entities
# ---------------------------------------------------------------------------

class TestHandleResult:
    def test_success_when_already_available_no_state_write(self):
        entity = _make_switch()
        entity._attr_available = True
        entity._handle_result(True)
        entity.async_write_ha_state.assert_not_called()

    def test_success_when_unavailable_marks_available(self):
        entity = _make_switch()
        entity._attr_available = False
        entity._handle_result(True)
        assert entity._attr_available is True

    def test_success_when_unavailable_writes_state(self):
        entity = _make_switch()
        entity._attr_available = False
        entity._handle_result(True)
        entity.async_write_ha_state.assert_called_once()

    def test_failure_marks_unavailable(self):
        entity = _make_switch()
        entity._handle_result(False)
        assert entity._attr_available is False

    def test_failure_writes_state(self):
        entity = _make_switch()
        entity._handle_result(False)
        entity.async_write_ha_state.assert_called_once()

    def test_failure_schedules_reconnect(self):
        entity = _make_switch()
        entity._reconnect_task = None
        entity._handle_result(False)
        entity.hass.async_create_task.assert_called_once()

    def test_failure_does_not_duplicate_running_reconnect(self):
        entity = _make_switch()
        running = MagicMock()
        running.done.return_value = False
        entity._reconnect_task = running
        entity._handle_result(False)
        entity.hass.async_create_task.assert_not_called()

    def test_failure_reschedules_after_completed_reconnect(self):
        entity = _make_switch()
        done = MagicMock()
        done.done.return_value = True
        entity._reconnect_task = done
        entity._handle_result(False)
        entity.hass.async_create_task.assert_called_once()


# ---------------------------------------------------------------------------
# Switch defaults
# ---------------------------------------------------------------------------

class TestSwitch:
    def test_available_by_default(self):
        assert _make_switch()._attr_available is True

    def test_not_on_by_default(self):
        assert _make_switch().is_on is False

    def test_unique_id(self):
        assert _make_switch()._attr_unique_id == "c4_amp_192.168.1.100_ch1_power"

    def test_name(self):
        assert _make_switch()._attr_name == "Test Zone Power"


# ---------------------------------------------------------------------------
# Volume slider
# ---------------------------------------------------------------------------

class TestVolumeSlider:
    def test_available_by_default(self):
        assert _make_slider()._attr_available is True

    def test_native_value_defaults_to_half(self):
        assert _make_slider().native_value == 0.5

    def test_min_max_step_class_attrs(self):
        entity = _make_slider()
        assert entity._attr_native_min_value == 0.0
        assert entity._attr_native_max_value == 1.0
        assert entity._attr_native_step == 0.01

    def test_unique_id(self):
        assert _make_slider()._attr_unique_id == "c4_amp_192.168.1.100_ch1_volume"

    def test_handle_result_marks_unavailable(self):
        entity = _make_slider()
        entity._handle_result(False)
        assert entity._attr_available is False


# ---------------------------------------------------------------------------
# Source select
# ---------------------------------------------------------------------------

class TestSourceSelect:
    def test_options_from_config(self):
        entity = _make_select()
        assert entity._attr_options == ["WiiM", "TV"]

    def test_current_option_none_by_default(self):
        assert _make_select().current_option is None

    def test_unique_id(self):
        assert _make_select()._attr_unique_id == "c4_amp_192.168.1.100_ch1_source"

    def test_handle_result_marks_unavailable(self):
        entity = _make_select()
        entity._handle_result(False)
        assert entity._attr_available is False


# ---------------------------------------------------------------------------
# Media player
# ---------------------------------------------------------------------------

class TestMediaPlayer:
    def test_available_by_default(self):
        assert _make_player()._attr_available is True

    def test_source_list_from_config(self):
        assert _make_player()._attr_source_list == ["WiiM", "TV"]

    def test_state_off_by_default(self):
        assert _make_player().state == "off"

    def test_unique_id(self):
        assert _make_player()._attr_unique_id == "c4_amp_192.168.1.100_ch1_player"

    def test_supported_features(self):
        # TURN_ON=1, TURN_OFF=2, SELECT_SOURCE=4 from our stub → 7
        assert _make_player()._attr_supported_features == 7

    def test_handle_result_marks_unavailable(self):
        entity = _make_player()
        entity._handle_result(False)
        assert entity._attr_available is False
