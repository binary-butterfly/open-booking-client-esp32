import uos
from machine import Pin, Timer
from app.extensions import config, wifi
from app.websocket import websocket_send


class Device:
    door_status = False
    lock_status = 'closed'
    door_status_detection = False

    def __init__(self):
        self.door_status_timer = Timer(1)
        self.door_status_pin = Pin(config.DOOR_STATUS_PIN, Pin.IN)
        self.door_status_pin.irq(self.trigger_door_status)
        self.lock_open_pin = Pin(config.LOCK_OPEN_PIN, Pin.OUT)
        self.lock_close_pin = Pin(config.LOCK_CLOSE_PIN, Pin.OUT)
        self.door_lock_timer = Timer(2)

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
        if self.lock_status in ['opening', 'closing']:
            return
        self.lock_status = 'opening'
        self.lock_open_pin.value(1)
        self.door_lock_timer.init(mode=Timer.ONE_SHOT, period=250, callback=self.finalize_lock)
        websocket_send('ResourceStatusChange', 'request', {'status': 'opening', 'resource_uid': config.RESOURCE_UID})

    def close_lock(self):
        if self.lock_status in ['opening', 'closing']:
            return
        self.lock_status = 'closing'
        self.lock_close_pin.value(1)
        self.door_lock_timer.init(mode=Timer.ONE_SHOT, period=250, callback=self.finalize_lock)
        websocket_send('ResourceStatusChange', 'request', {'status': 'closing', 'resource_uid': config.RESOURCE_UID})

    def finalize_lock(self, pin):
        self.lock_open_pin.value(0)
        self.lock_close_pin.value(0)
        if self.lock_status == 'opening':
            self.lock_status = 'open'
        elif self.lock_status == 'closing':
            self.lock_status = 'closed'
        websocket_send(
            'ResourceStatusChange',
            'request',
            {'status': self.lock_status, 'resource_uid': config.RESOURCE_UID}
        )
