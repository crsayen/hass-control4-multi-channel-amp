import asyncio
import logging
import random
import socket

PORT = 8750

_LOGGER = logging.getLogger(__name__)


def _send_udp_command(cmd: str, host: str) -> None:
    counter = "0s2a" + str(random.randint(10, 99))
    fmt_cmd = f"{counter} {cmd} \r\n"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(fmt_cmd.encode("utf-8"), (host, PORT))
        sock.settimeout(1.0)
        sock.recvfrom(1024)
    finally:
        sock.close()


def pad_byte(i: int) -> str:
    return f"{i:#0{4}x}"[2:]


async def amp_channel_volume(amp_channel: int, volume: float, ip: str) -> bool:
    volume_hex = pad_byte(int(float(volume) * 100) + 160)
    try:
        await asyncio.to_thread(_send_udp_command, f"c4.amp.chvol {pad_byte(amp_channel)} {volume_hex}", ip)
    except OSError:
        _LOGGER.warning("No response from amp at %s", ip)
        return False
    return True


async def amp_channel_on(amp_channel: int, amp_input: int, ip: str) -> bool:
    try:
        await asyncio.to_thread(
            _send_udp_command,
            f"c4.amp.out {pad_byte(amp_channel)} {pad_byte(int(amp_input))}",
            ip,
        )
    except OSError:
        _LOGGER.warning("No response from amp at %s", ip)
        return False
    return True


async def amp_channel_off(amp_channel: int, ip: str) -> bool:
    try:
        await asyncio.to_thread(_send_udp_command, f"c4.amp.out {pad_byte(amp_channel)} 00", ip)
    except OSError:
        _LOGGER.warning("No response from amp at %s", ip)
        return False
    return True
