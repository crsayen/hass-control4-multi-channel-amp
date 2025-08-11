import socket
import random

PORT = 8750

def send_udp_command(cmd, host):
    counter = '0s2a' + str(random.randint(10, 99))
    fmt_cmd = counter + ' ' + cmd + ' \r\n'

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(fmt_cmd.encode('utf-8'), (host, PORT))

def pad_byte(i):
    return f"{i:#0{4}x}"[2:]

def amp_channel_volume(amp_channel, volume, ip):
    volume_hex = pad_byte(int(float(volume) * 100) + 160)
    send_udp_command(f'c4.amp.chvol {pad_byte(amp_channel)} {volume_hex}', ip)

def amp_channel_on(amp_channel, amp_input, ip):
    send_udp_command(f'c4.amp.out {pad_byte(amp_channel)} {pad_byte(int(amp_input))}', ip)

def amp_channel_off(amp_channel, ip):
    send_udp_command(f'c4.amp.out {pad_byte(amp_channel)} 00', ip)
