import udp_commands

class Channel:
    def __init__(self, ip, channel, port, sources):
        self.ip = ip
        self.channel = channel
        self.port = port
        self.sources = sources
        self.selected_source = sources['WiiM']
    
    def on(self):
        resp = udp_commands.amp_channel_on(self.channel, self.selected_source, self.ip)
        print(f'channel {self.channel} turned on:\n\t{resp}')
        return resp
    
    def off(self):
        resp = udp_commands.amp_channel_off(self.channel, self.ip)
        print(f'channel {self.channel} turned off:\n\t{resp}')
        return resp
    
    def setVolume(self, volume):
        scaled_volume = volume / 100
        v = max(min(scaled_volume, 1.0), 0.0)
        resp = udp_commands.amp_channel_volume(self.channel, v, self.ip)
        print(f'channel {self.channel} volume {volume}:\n\t{resp}')
        return resp