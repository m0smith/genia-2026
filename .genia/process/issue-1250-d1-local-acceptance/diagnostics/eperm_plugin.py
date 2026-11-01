import _socket, errno
_orig = _socket.socket.__init__
def _eperm(self, *a, **k):
    raise PermissionError(errno.EPERM, "Operation not permitted")
import socket
socket.socket.__init__ = _eperm
