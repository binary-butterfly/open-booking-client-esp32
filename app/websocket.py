import uos
import ujson as json
from ubinascii import hexlify
from app.extensions import websocket_send_queue
from app import config


def websocket_send(message_type, state, data, uid=None):
    to_send = json.dumps({
        'state': state,
        'type': message_type,
        'uid': hexlify(uos.urandom(16)).decode() if uid is None else uid,
        'data': data
    })
    if config.DEBUG:
        print('>> %s' % to_send)
    websocket_send_queue.append(to_send)
