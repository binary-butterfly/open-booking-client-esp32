import uos
import ussl
import usocket

host = 'raw.githubusercontent.com'
CHUNK_SIZE = 512

from app.networking import wifi_connect


def get(path, save_to_file=None):
    ai = usocket.getaddrinfo(host, 443, 0, usocket.SOCK_STREAM)
    if len(ai) < 1:
        raise ValueError('You are not connected to the internet...')
    ai = ai[0]

    s = usocket.socket(ai[0], ai[1], ai[2])
    try:
        s.connect(ai[-1])
        s = ussl.wrap_socket(s, server_hostname=host)
        s.write(b'GET %s HTTP/1.0\r\n' % path)
        s.write(b'Host: %s\r\n' % host)
        s.write(b'Accept: */*\r\n')
        s.write(b'User-Agent: MicroPython Client\r\n\r\n')

        while True:
            line = s.readline()
            if not line or line == b'\r\n':
                break
    except OSError:
        s.close()
        raise
    if save_to_file is None:
        result = s.read()
        s.close()
        return result

    with open(save_to_file, 'w') as outfile:
        data = s.read(CHUNK_SIZE)
        while data:
            outfile.write(data)
            data = s.read(CHUNK_SIZE)
        outfile.close()
    s.close()


def ensure_dir(dir):
    try:
        uos.stat(dir)
    except OSError:
        uos.mkdir(dir)


def update(version):
    wifi_connect()
    ensure_dir('/next')
    base_path = '/binary-butterfly/open-booking-client-esp32/%s' % version
    file_paths = get('%s/update-file-list' % base_path).split(b'\n')
    for file_path in file_paths:
        if not file_path or file_path[0:4] != 'app/':
            continue
        get(b'%s/%s' % (base_path, file_path), b'/next/%s' % file_path[4:])
