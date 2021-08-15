import network
from app.extensions import config


def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        if config.DEBUG:
            print('wifi already connected, proceed ...')
        return wlan
    if config.DEBUG:
        print('connecting to wifi ...')
    wlan.connect(config.WIFI_NETWORK, config.WIFI_PASSWORD)
    while not wlan.isconnected():
        pass
    if config.DEBUG:
        print('wifi connected.')
    return wlan
