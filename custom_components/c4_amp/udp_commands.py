import asyncio
import logging
import random
import socket
import threading

DEFAULT_PORT = 8750

_LOGGER = logging.getLogger(__name__)


UDP_TIMEOUT = 0.05  # 50ms per attempt
UDP_RETRIES = 3  # total attempts = 1 + retries


class CommandCancelled(Exception):
    """Raised when a UDP command is cancelled by a newer command."""


def cancel_and_replace(data: dict) -> threading.Event:
    """Cancel any in-flight command for this channel and return a fresh Event."""
    old = data.get("cancel")
    if old is not None:
        old.set()
    new_cancel = threading.Event()
    data["cancel"] = new_cancel
    return new_cancel


def _send_udp_command(cmd: str, host: str, port: int, cancel: threading.Event | None = None) -> None:
    counter = "0s2a" + str(random.randint(10, 99))
    fmt_cmd = f"{counter} {cmd} \r\n"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(UDP_TIMEOUT)
    try:
        for attempt in range(1 + UDP_RETRIES):
            if cancel and cancel.is_set():
                raise CommandCancelled()
            sock.sendto(fmt_cmd.encode("utf-8"), (host, port))
            try:
                sock.recvfrom(1024)
                return
            except socket.timeout:
                if attempt < UDP_RETRIES:
                    _LOGGER.debug(
                        "No response from %s:%s (attempt %d/%d), retrying",
                        host, port, attempt + 1, 1 + UDP_RETRIES,
                    )
        raise OSError(f"No response from {host}:{port} after {1 + UDP_RETRIES} attempts")
    finally:
        sock.close()


def pad_byte(i: int) -> str:
    return f"{i:#0{4}x}"[2:]


async def amp_channel_volume(
    amp_channel: int, volume: float, ip: str, port: int = DEFAULT_PORT,
    cancel: threading.Event | None = None,
) -> bool | None:
    volume_hex = pad_byte(int(float(volume) * 100) + 160)
    try:
        await asyncio.to_thread(
            _send_udp_command, f"c4.amp.chvol {pad_byte(amp_channel)} {volume_hex}", ip, port, cancel,
        )
    except CommandCancelled:
        return None
    except OSError:
        _LOGGER.warning("No response from amp at %s:%s", ip, port)
        return False
    return True


async def amp_channel_on(
    amp_channel: int, amp_input: int, ip: str, port: int = DEFAULT_PORT,
    cancel: threading.Event | None = None,
) -> bool | None:
    try:
        await asyncio.to_thread(
            _send_udp_command,
            f"c4.amp.out {pad_byte(amp_channel)} {pad_byte(int(amp_input))}",
            ip, port, cancel,
        )
    except CommandCancelled:
        return None
    except OSError:
        _LOGGER.warning("No response from amp at %s:%s", ip, port)
        return False
    return True


async def amp_channel_off(
    amp_channel: int, ip: str, port: int = DEFAULT_PORT,
    cancel: threading.Event | None = None,
) -> bool | None:
    try:
        await asyncio.to_thread(
            _send_udp_command, f"c4.amp.out {pad_byte(amp_channel)} 00", ip, port, cancel,
        )
    except CommandCancelled:
        return None
    except OSError:
        _LOGGER.warning("No response from amp at %s:%s", ip, port)
        return False
    return True
