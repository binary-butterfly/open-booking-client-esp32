import network
from app import config


def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(config.WIFI_NETWORK, config.WIFI_PASSWORD)
        while not wlan.isconnected():
            pass
    return wlan
