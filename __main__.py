import yaml
from channel import Channel
import time



lr = Channel('192.168.0.145', 1, 8750, {'WiiM': 2})

# bedroom.on()
# time.sleep(1)
# bedroom.setVolume(15)
# time.sleep(1)
# bedroom.off()
lr.on()
time.sleep(1)
lr.setVolume(5)
time.sleep(1)
lr.setVolume(10)
time.sleep(1)
lr.off()