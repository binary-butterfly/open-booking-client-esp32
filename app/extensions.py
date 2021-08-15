from .config import Config
config = Config()

websocket_send_queue = []
websocket_receive_queue = []

from app.networking import wifi_connect
wifi = wifi_connect()

from app.websocket_client import WebsocketClient
websocket = WebsocketClient()

from app.device import Device
device = Device()
