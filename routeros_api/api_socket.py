import socket
from routeros_api import exceptions
try:
    import errno
except ImportError:
    errno = None

EINTR = getattr(errno, 'EINTR', 4)

def get_socket(hostname, port):
    api_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    api_socket.settimeout(15.0)
    api_socket.connect((hostname, port))
    set_keepalive(api_socket, after_idle_sec=10)
    return SocketWrapper(api_socket)

# http://stackoverflow.com/a/14855726
def set_keepalive(sock, after_idle_sec=1, interval_sec=3, max_fails=5):
    """Set TCP keepalive on an open socket.

    It activates after 1 second (after_idle_sec) of idleness,
    then sends a keepalive ping once every 3 seconds (interval_sec),
    and closes the connection after 5 failed ping (max_fails), or 15 seconds
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)


class SocketWrapper(object):
    def __init__(self, socket):
        self.socket = socket

    def send(self, bytes):
        return self.socket.sendall(bytes)

    def receive(self, length):
        while True:
            try:
                return self.socket.recv(length)
            except socket.error as e:
                if e.args[0] == EINTR:
                    continue
                else:
                    raise

    def close(self):
        return self.socket.close()


class CloseConnectionExceptionHandler:
    def __init__(self, socket):
        self.socket = socket

    def handle(self, exception):
        connection_closed = isinstance(
            exception, exceptions.RouterOsApiConnectionClosedError)
        fatal_error = isinstance(exception, exceptions.FatalRouterOsApiError)
        if connection_closed or fatal_error:
            self.socket.close()