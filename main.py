import network
from machine import idle

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
nets = wlan.scan()
for net in nets:
    if net[0] == b'':
        wlan.connect('', '')
        while not wlan.isconnected():
            idle()
        break

if wlan.isconnected():
    import th
