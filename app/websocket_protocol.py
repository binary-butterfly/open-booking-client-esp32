"""
Websockets protocol

MIT License

Copyright (c) 2019 Danielle Madeley, 2021 binary butterfly GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import uselect
import ustruct as struct
import urandom as random
from ubinascii import hexlify

# Opcodes
OP_CONT = const(0x0)
OP_TEXT = const(0x1)
OP_BYTES = const(0x2)
OP_CLOSE = const(0x8)
OP_PING = const(0x9)
OP_PONG = const(0xa)

# Close codes
CLOSE_OK = const(1000)
CLOSE_GOING_AWAY = const(1001)
CLOSE_PROTOCOL_ERROR = const(1002)
CLOSE_DATA_NOT_SUPPORTED = const(1003)
CLOSE_BAD_DATA = const(1007)
CLOSE_POLICY_VIOLATION = const(1008)
CLOSE_TOO_BIG = const(1009)
CLOSE_MISSING_EXTN = const(1010)
CLOSE_BAD_CONDITION = const(1011)


class NoDataException(Exception):
    pass


class ConnectionClosed(Exception):
    pass


class Websocket:
    """
    Basis of the Websocket protocol.

    This can probably be replaced with the C-based websocket module, but
    this one currently supports more options.
    """
    is_client = True

    def __init__(self, sock, timeout):
        self.sock = sock
        self.sock.setblocking(False)
        self.open = True
        self.timeout = timeout
        self.poller = uselect.poll()
        self.poller.register(sock, uselect.POLLIN)
        self.input = b''

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def poll(self):
        res = self.poller.poll(1)
        if not res:
            return
        fragment = None
        for sock, ev in res:
            if ev & (uselect.POLLHUP | uselect.POLLERR):
                self._close()
                raise ConnectionClosed()
            fragment = sock.read()
        if not fragment:
            self._close()
            raise ConnectionClosed()
        self.input += fragment
        return self.handle_input()

    def handle_input(self):
        """
        parses message and looks if message is complete
        """
        position = 2
        if len(self.input) < position:  # 2 start
            return
        two_bytes = self.input[0:2]
        byte1, byte2 = struct.unpack('!BB', two_bytes)

        # Byte 1: FIN(1) _(1) _(1) _(1) OPCODE(4)
        fin = bool(byte1 & 0x80)
        opcode = byte1 & 0x0f

        # Byte 2: MASK(1) LENGTH(7)
        mask = bool(byte2 & (1 << 7))
        length = byte2 & 0x7f

        if length == 126:  # Magic number, length header is 2 bytes
            position += 2
            if len(self.input) < position: # 2 start bytes + 2 header bytes
                return
            length, = struct.unpack('!H', self.input[2:4])
        elif length == 127:  # Magic number, length header is 8 bytes
            position += 8
            if len(self.input) < position: # 2 start bytes + 8 header bytes
                return
            length, = struct.unpack('!Q', self.input[2:10])

        if mask:  # Mask is 4 bytes
            position += 4
            if len(self.input) < position:
                return
            mask_bits = self.input[position - 4:position]
        if len(self.input) < position + length:
            return
        try:
            data = self.input[position:position + length]
            self.input = self.input[position + length:]
        except MemoryError:
            # We can't receive this many bytes, close the socket
            self.close(code=CLOSE_TOO_BIG)
            return

        if mask:
            data = bytes(b ^ mask_bits[i % 4] for i, b in enumerate(data))

        if not fin:
            raise NotImplementedError()

        if opcode == OP_TEXT:
            return data.decode('utf-8')
        if opcode == OP_BYTES:
            return data
        if opcode == OP_CLOSE:
            self._close()
            return
        if opcode == OP_PONG:
            # Ignore this frame, keep waiting for a data frame
            return
        if opcode == OP_PING:
            # We need to send a pong frame
            self.write_frame(OP_PONG, data)
            # And then wait to receive
            return
        if opcode == OP_CONT:
            # This is a continuation of a previous frame
            raise NotImplementedError(opcode)
        raise ValueError(opcode)


    def read_frame(self):
        two_bytes = None
        # Frame header
        try:
            res = self.poller.poll(100)
            if not res:
                raise NoDataException
            for sock, ev in res:
                print(ev)
                if ev & (uselect.POLLHUP | uselect.POLLERR):
                    raise ValueError
                two_bytes = sock.read(2)
        except OSError:
            raise NoDataException
        if not two_bytes:
            raise ValueError

        byte1, byte2 = struct.unpack('!BB', two_bytes)

        # Byte 1: FIN(1) _(1) _(1) _(1) OPCODE(4)
        fin = bool(byte1 & 0x80)
        opcode = byte1 & 0x0f

        # Byte 2: MASK(1) LENGTH(7)
        mask = bool(byte2 & (1 << 7))
        length = byte2 & 0x7f

        if length == 126:  # Magic number, length header is 2 bytes
            length, = struct.unpack('!H', self.sock.read(2))
        elif length == 127:  # Magic number, length header is 8 bytes
            length, = struct.unpack('!Q', self.sock.read(8))

        if mask:  # Mask is 4 bytes
            mask_bits = sock.read(4)
        try:
            data = sock.read(length)
        except MemoryError:
            # We can't receive this many bytes, close the socket
            self.close(code=CLOSE_TOO_BIG)
            return True, OP_CLOSE, None

        if mask:
            data = bytes(b ^ mask_bits[i % 4] for i, b in enumerate(data))

        return fin, opcode, data

    def write_frame(self, opcode, data=b''):
        """
        Write a frame to the socket.
        See https://tools.ietf.org/html/rfc6455#section-5.2 for the details.
        """
        fin = True
        mask = self.is_client  # messages sent by client are masked

        length = len(data)

        # Frame header
        # Byte 1: FIN(1) _(1) _(1) _(1) OPCODE(4)
        byte1 = 0x80 if fin else 0
        byte1 |= opcode

        # Byte 2: MASK(1) LENGTH(7)
        byte2 = 0x80 if mask else 0

        if length < 126:  # 126 is magic value to use 2-byte length header
            byte2 |= length
            self.sock.write(struct.pack('!BB', byte1, byte2))

        elif length < (1 << 16):  # Length fits in 2-bytes
            byte2 |= 126  # Magic code
            self.sock.write(struct.pack('!BBH', byte1, byte2, length))

        elif length < (1 << 64):
            byte2 |= 127  # Magic code
            self.sock.write(struct.pack('!BBQ', byte1, byte2, length))

        else:
            raise ValueError()

        if mask:  # Mask is 4 bytes
            mask_bits = struct.pack('!I', random.getrandbits(32))
            self.sock.write(mask_bits)

            data = bytes(b ^ mask_bits[i % 4]
                         for i, b in enumerate(data))

        self.sock.write(data)

    def recv(self):
        """
        Receive data from the websocket.

        This is slightly different from 'websockets' in that it doesn't
        fire off a routine to process frames and put the data in a queue.
        If you don't call recv() sufficiently often you won't process control
        frames.
        """
        assert self.open

        while self.open:
            try:
                fin, opcode, data = self.read_frame()
            except NoDataException:
                return None
            except ValueError:
                self._close()
                raise ConnectionClosed()

            if not fin:
                raise NotImplementedError()

            if opcode == OP_TEXT:
                return data.decode('utf-8')
            elif opcode == OP_BYTES:
                return data
            elif opcode == OP_CLOSE:
                self._close()
                return
            elif opcode == OP_PONG:
                # Ignore this frame, keep waiting for a data frame
                continue
            elif opcode == OP_PING:
                # We need to send a pong frame
                self.write_frame(OP_PONG, data)
                # And then wait to receive
                continue
            elif opcode == OP_CONT:
                # This is a continuation of a previous frame
                raise NotImplementedError(opcode)
            else:
                raise ValueError(opcode)

    def send(self, buf):
        """Send data to the websocket."""

        assert self.open

        if isinstance(buf, str):
            opcode = OP_TEXT
            buf = buf.encode('utf-8')
        elif isinstance(buf, bytes):
            opcode = OP_BYTES
        else:
            raise TypeError()

        self.write_frame(opcode, buf)

    def close(self, code=CLOSE_OK, reason=''):
        """Close the websocket."""
        if not self.open:
            return

        buf = struct.pack('!H', code) + reason.encode('utf-8')

        self.write_frame(OP_CLOSE, buf)
        self._close()

    def _close(self):
        print('closed!')
        self.open = False
        self.poller.unregister(self.sock)
        self.sock.close()
