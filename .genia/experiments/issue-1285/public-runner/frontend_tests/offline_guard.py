"""Verification-only Linux/amd64 guard: deny socket/connect across child exec.

Adds restrictions to the inherited host policy; never changes proxy/routing or
grants network access. Stdlib ctypes installs a small seccomp filter after
PR_SET_NO_NEW_PRIVS. A real socket negative control must fail before exec. This
is not a general sandbox or a replacement for target network/venue receipts.
"""

import ctypes
import errno
import os
import platform
import socket
import sys


class Filter(ctypes.Structure):
    """Linux sock_filter instruction layout for classic BPF seccomp input."""

    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]


class Program(ctypes.Structure):
    """Linux sock_fprog descriptor; instruction storage survives prctl()."""

    _fields_ = [("length", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]


def main():
    """Apply only restrictive policy, prove denied Internet socket, exec exact argv."""
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("offline guard requires Linux/amd64")
    instructions = [
        (0x20, 0, 0, 4),
        (0x15, 1, 0, 0xC000003E),
        (0x06, 0, 0, 0x80000000),
        (0x20, 0, 0, 0),
        (0x15, 0, 1, 41),
        (0x06, 0, 0, 0x00050000 | errno.EPERM),
        (0x15, 0, 1, 42),
        (0x06, 0, 0, 0x00050000 | errno.EPERM),
        (0x06, 0, 0, 0x7FFF0000),
    ]
    filters = (Filter * len(instructions))(*(Filter(*row) for row in instructions))
    program = Program(len(filters), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) or libc.prctl(22, 2, ctypes.byref(program), 0, 0):
        raise OSError(ctypes.get_errno(), "restrictive seccomp unavailable")
    try:
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except PermissionError as error:
        if error.errno != errno.EPERM:
            raise
    else:
        raise RuntimeError("socket negative control did not fail")
    print(
        "OFFLINE_GUARD: socket EPERM; socket/connect denial inherited across exec",
        file=sys.stderr,
        flush=True,
    )
    argv = sys.argv[1:]
    if not argv:
        raise ValueError("missing child argv")
    os.execvpe(argv[0], argv, os.environ)


if __name__ == "__main__":
    main()
