import uos
import ujson as json
from ubinascii import hexlify
from app.extensions import websocket_send_queue


def websocket_send(message_type, state, data, uid=None):
    websocket_send_queue.append(json.dumps({
        'state': state,
        'type': message_type,
        'uid': hexlify(uos.urandom(16)).decode() if uid is None else uid,
        'data': data
    }))
