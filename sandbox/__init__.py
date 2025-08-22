import yaml
from channel import Channel
import time

with open("amp_channels.yaml", "r") as f:
    channels: dict[str, Channel] = {
        k:
        Channel(v['ip'], v['channel'], v['port'], v['sources'])
        for k,v in yaml.safe_load(f)['c4_amp'].items()
    }

bedroom = channels.get('Bedroom')
casa = channels.get('Casa Shea')

# bedroom.on()
# time.sleep(1)
# bedroom.setVolume(15)
# time.sleep(1)
# bedroom.off()
casa.on()
time.sleep(1)
casa.setVolume(15)
time.sleep(1)
casa.off()