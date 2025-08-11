# custom_components/c4_amp/helpers.py

import socket
import random

DOMAIN = "c4_amp"
DEFAULT_PORT = 8750

def pad_byte(i):
    return f"{i:#0{4}x}"[2:]

def send_udp_command(ip_address, port, cmd):
    counter = '0s2a' + str(random.randint(10, 99))
    fmt_cmd = counter + ' ' + cmd + ' \r\n'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(fmt_cmd.encode(), (ip_address, port))
        sock.settimeout(1.0)
        data, _ = sock.recvfrom(1024)
        return data.decode()
    except socket.timeout:
        return None
    finally:
        sock.close()

def amp_channel_volume(ip, port, amp_channel, volume):
    volume_hex = pad_byte(int(float(volume) * 100) + 160)
    return send_udp_command(ip, port, f'c4.amp.chvol {pad_byte(amp_channel)} {volume_hex}')

def amp_channel_on(ip, port, amp_channel, amp_input):
    return send_udp_command(ip, port, f'c4.amp.out {pad_byte(amp_channel)} {pad_byte(amp_input)}')

def amp_channel_off(ip, port, amp_channel):
    return send_udp_command(ip, port, f'c4.amp.out {pad_byte(amp_channel)} 00')
