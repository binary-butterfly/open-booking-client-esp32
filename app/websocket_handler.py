import machine
from time import sleep
import ujson as json
from app.extensions import config, device
from app.websocket import websocket_send
from app.update import update


class HandleWebsocketMessage:
    def __init__(self, message_raw):
        if config.DEBUG:
            print('<< %s' % message_raw)
        message = json.loads(message_raw)
        self.state = message['state']
        self.uid = message['uid']
        self.type = message['type']
        self.data = message['data']
        if hasattr(self, 'handle%sR%s' % (self.type, self.state[1:])):
            getattr(self, 'handle%sR%s' % (self.type, self.state[1:]))()

    def handleRemoteChangeResourceStatusRequest(self):
        if self.data['status'] == 'open':
            device.open_lock()
        else:
            device.close_lock()
        websocket_send(self.type, 'reply', {}, self.uid)

    def handleReboot(self):
        websocket_send(self.type, 'reply', {}, self.uid)
        sleep(1)
        machine.reset()

    def handleFirmwareUpdate(self):
        update(self.data['version'])
