"""Tests for YAML configuration schema validation."""
import pytest
import voluptuous as vol

from custom_components.c4_amp import CONFIG_SCHEMA, DOMAIN
from custom_components.c4_amp.udp_commands import DEFAULT_PORT


def _zone(overrides=None):
    base = {"ip": "192.168.1.100", "channel": 1}
    if overrides:
        base.update(overrides)
    return {DOMAIN: {"Living Room": base}}


class TestValidConfigs:
    def test_minimal_config_accepted(self):
        result = CONFIG_SCHEMA(_zone())
        zone = result[DOMAIN]["Living Room"]
        assert zone["ip"] == "192.168.1.100"
        assert zone["channel"] == 1

    def test_default_port_applied(self):
        result = CONFIG_SCHEMA(_zone())
        assert result[DOMAIN]["Living Room"]["port"] == DEFAULT_PORT

    def test_default_sources_empty(self):
        result = CONFIG_SCHEMA(_zone())
        assert result[DOMAIN]["Living Room"]["sources"] == {}

    def test_port_override(self):
        result = CONFIG_SCHEMA(_zone({"port": 9000}))
        assert result[DOMAIN]["Living Room"]["port"] == 9000

    def test_sources_accepted(self):
        result = CONFIG_SCHEMA(_zone({"sources": {1: "WiiM", 2: "TV"}}))
        assert result[DOMAIN]["Living Room"]["sources"] == {1: "WiiM", 2: "TV"}

    def test_channel_coerced_from_string(self):
        result = CONFIG_SCHEMA(_zone({"channel": "3"}))
        assert result[DOMAIN]["Living Room"]["channel"] == 3

    def test_multiple_zones(self):
        config = {
            DOMAIN: {
                "Zone A": {"ip": "192.168.1.1", "channel": 1},
                "Zone B": {"ip": "192.168.1.1", "channel": 2},
            }
        }
        result = CONFIG_SCHEMA(config)
        assert len(result[DOMAIN]) == 2

    def test_extra_top_level_keys_allowed(self):
        config = {
            DOMAIN: {"Zone A": {"ip": "192.168.1.1", "channel": 1}},
            "other_integration": {"foo": "bar"},
        }
        result = CONFIG_SCHEMA(config)
        assert "other_integration" in result


class TestInvalidConfigs:
    def test_missing_ip_raises(self):
        with pytest.raises(vol.MultipleInvalid):
            CONFIG_SCHEMA({DOMAIN: {"Zone": {"channel": 1}}})

    def test_missing_channel_raises(self):
        with pytest.raises(vol.MultipleInvalid):
            CONFIG_SCHEMA({DOMAIN: {"Zone": {"ip": "192.168.1.1"}}})

    def test_channel_zero_raises(self):
        with pytest.raises(vol.MultipleInvalid):
            CONFIG_SCHEMA(_zone({"channel": 0}))

    def test_channel_nine_raises(self):
        with pytest.raises(vol.MultipleInvalid):
            CONFIG_SCHEMA(_zone({"channel": 9}))

    def test_channel_eight_accepted(self):
        result = CONFIG_SCHEMA(_zone({"channel": 8}))
        assert result[DOMAIN]["Living Room"]["channel"] == 8
