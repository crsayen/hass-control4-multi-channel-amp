"""Tests for UDP command formatting and error handling."""
import pytest
from unittest.mock import patch

from custom_components.c4_amp.udp_commands import (
    DEFAULT_PORT,
    amp_channel_off,
    amp_channel_on,
    amp_channel_volume,
    pad_byte,
)


class TestPadByte:
    def test_zero(self):
        assert pad_byte(0) == "00"

    def test_one(self):
        assert pad_byte(1) == "01"

    def test_eight(self):
        assert pad_byte(8) == "08"

    def test_fifteen(self):
        assert pad_byte(15) == "0f"

    def test_volume_at_zero(self):
        # volume 0.0 -> int(0) + 160 = 160 = 0xa0
        assert pad_byte(int(0.0 * 100) + 160) == "a0"

    def test_volume_at_half(self):
        # volume 0.5 -> int(50) + 160 = 210 = 0xd2
        assert pad_byte(int(0.5 * 100) + 160) == "d2"

    def test_volume_at_one(self):
        # volume 1.0 -> int(100) + 160 = 260 = 0x104
        assert pad_byte(int(1.0 * 100) + 160) == "104"


class TestAmpChannelVolume:
    async def test_correct_command_string(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command") as mock:
            await amp_channel_volume(1, 0.5, "192.168.1.1")
            cmd = mock.call_args[0][0]
            assert cmd == "c4.amp.chvol 01 d2"

    async def test_channel_is_padded(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command") as mock:
            await amp_channel_volume(8, 0.0, "192.168.1.1")
            cmd = mock.call_args[0][0]
            assert cmd.startswith("c4.amp.chvol 08 ")

    async def test_uses_provided_host_and_port(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command") as mock:
            await amp_channel_volume(1, 0.5, "10.0.0.1", 9000)
            assert mock.call_args[0][1] == "10.0.0.1"
            assert mock.call_args[0][2] == 9000

    async def test_uses_default_port_when_omitted(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command") as mock:
            await amp_channel_volume(1, 0.5, "10.0.0.1")
            assert mock.call_args[0][2] == DEFAULT_PORT

    async def test_returns_true_on_success(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command"):
            assert await amp_channel_volume(1, 0.5, "192.168.1.1") is True

    async def test_returns_false_on_os_error(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command", side_effect=OSError):
            assert await amp_channel_volume(1, 0.5, "192.168.1.1") is False


class TestAmpChannelOn:
    async def test_correct_command_string(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command") as mock:
            await amp_channel_on(2, 3, "192.168.1.1")
            cmd = mock.call_args[0][0]
            assert cmd == "c4.amp.out 02 03"

    async def test_returns_true_on_success(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command"):
            assert await amp_channel_on(1, 1, "192.168.1.1") is True

    async def test_returns_false_on_os_error(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command", side_effect=OSError):
            assert await amp_channel_on(1, 1, "192.168.1.1") is False


class TestAmpChannelOff:
    async def test_correct_command_string(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command") as mock:
            await amp_channel_off(3, "192.168.1.1")
            cmd = mock.call_args[0][0]
            assert cmd == "c4.amp.out 03 00"

    async def test_returns_true_on_success(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command"):
            assert await amp_channel_off(1, "192.168.1.1") is True

    async def test_returns_false_on_os_error(self):
        with patch("custom_components.c4_amp.udp_commands._send_udp_command", side_effect=OSError):
            assert await amp_channel_off(1, "192.168.1.1") is False
