from app.extensions import config, websocket, websocket_send_queue, device
from app.websocket_handler import HandleWebsocketMessage
from app.websocket_protocol import NoDataException, ConnectionClosed
from app.websocket import websocket_send


def main_loop():
    if config.DEBUG:
        print('loading application ...')
    device.boot()

    while True:
        if not websocket.open:
            websocket.reconnect()
        try:
            if len(websocket_send_queue):
                websocket.send(websocket_send_queue.pop() + "\r\n")
            reply = websocket.poll()
            if reply is not None:
                HandleWebsocketMessage(reply)
        except (NoDataException, ConnectionClosed):
            continue
        except Exception as e:
            websocket_send('Exception', 'request', {'error': str(e)})




