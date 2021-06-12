import uos
from machine import Pin, Timer
from app import config
from app.extensions import wifi
from app.websocket import websocket_send


class Device:
    door_status = False
    lock_status = False
    door_status_detection = False

    def __init__(self):
        self.door_status_timer = Timer(1)
        self.door_status_pin = Pin(config.DOOR_STATUS_PIN, Pin.IN)
        self.door_status_pin.irq(self.trigger_door_status)
        self.lock_pin = Pin(config.LOCK_PIN, Pin.OUT)

    def trigger_door_status(self, pin):
        if not self.door_status_detection:
            self.door_status_timer.init(mode=Timer.ONE_SHOT, period=500, callback=self.finalize_door_status)

    def finalize_door_status(self, timer):
        self.door_status = self.door_status_pin.value() == 1
        self.door_status_timer.deinit()
        self.door_status_detection = False
        websocket_send('DoorStatus', 'request', {'status': self.door_status})

    def boot(self):
        system = uos.uname()
        wifi_ifconfig = wifi.ifconfig()
        websocket_send('BootNotification', 'request', {
            'sysname': system[0],
            'nodename': system[1],
            'release': system[2],
            'version': system[3],
            'machine': system[4],
            'ip': wifi_ifconfig[0],
            'subnet': wifi_ifconfig[1],
            'gateway': wifi_ifconfig[2],
            'dns': wifi_ifconfig[3]
        })

    def check_door_lock(self):
        if self.door_status != self.door_status_pin.value():
            self.door_status = not self.door_status
            websocket_send('DoorStatus', 'request', {'status': self.door_status})

    def open_lock(self):
        if self.lock_status:
            return
        self.lock_status = True
        self.lock_pin.value(1)
        websocket_send('ResourceStatusChange', 'request', {'status': 'open', 'resource_uid': config.RESOURCE_UID})

    def close_lock(self):
        if not self.lock_status:
            return
        self.lock_status = False
        self.lock_pin.value(0)
        websocket_send('ResourceStatusChange', 'request', {'status': 'closed', 'resource_uid': config.RESOURCE_UID})
