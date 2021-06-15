import ussl
import usocket as socket
import urandom as random
from ubinascii import hexlify, b2a_base64


from app import config
from app.websocket_protocol import Websocket
from app.websocket import websocket_send


class WebsocketClient:
    ws = None

    def __init__(self):
        while True:
            try:
                self.connect()
                break
            except OSError:
                continue

    def reconnect(self):
        while True:
            try:
                self.connect()
                break
            except OSError:
                continue
        websocket_send('ConnectionChange', 'request', {'status': 'reconnected'})

    def connect(self):
        sock = socket.socket()
        addr = socket.getaddrinfo(config.WEBSOCKET_HOSTNAME, config.WEBSOCKET_PORT)
        sock.connect(addr[0][4])
        if config.WEBSOCKET_TLS:
            sock = ussl.wrap_socket(sock)

        def send_header(header, *args):
            sock.write(header % args + '\r\n')

        # Sec-WebSocket-Key is 16 bytes of random base64 encoded
        key = b2a_base64(bytes(random.getrandbits(8) for _ in range(16)))[:-1]

        send_header(b'GET %s HTTP/1.1', config.WEBSOCKET_PATH or '/')
        send_header(b'Host: %s:%s', config.WEBSOCKET_HOSTNAME, config.WEBSOCKET_PORT)
        send_header(b'Connection: Upgrade')
        send_header(b'Upgrade: websocket')
        send_header(b'Sec-WebSocket-Key: %s', key)
        send_header(b'Sec-WebSocket-Version: 13')
        send_header(b'Origin: http://%s:%s' % (config.WEBSOCKET_HOSTNAME, config.WEBSOCKET_PORT))
        send_header(b'Authorization: Basic %s' % b2a_base64(b'%s:%s' % (
            config.WEBSOCKET_USER,
            config.WEBSOCKET_PASSWORD
        ))[:-1])
        send_header(b'')

        header = sock.readline()[:-2]
        assert header.startswith(b'HTTP/1.1 101 '), header

        while header:
            header = sock.readline()[:-2]
        print('connected!')
        self.ws = Websocket(sock, 0.1)

    def send(self, buf):
        return self.ws.send(buf)

    def recv(self):
        return self.ws.recv()

    @property
    def open(self):
        return self.ws and self.ws.open

