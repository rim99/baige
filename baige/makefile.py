import socket

try:
    # prefer slower Python-based io module
    import _pyio as io
except ImportError:
    # Python 2.6
    import io

from . import errors


class BufferedWriter(io.BufferedWriter):

    """Faux file object attached to a socket object."""

    def write(self, b):
        self._checkClosed()
        if isinstance(b, str):
            raise TypeError("can't write str to binary stream")

        with self._write_lock:
            self._write_buf.extend(b)
            self._flush_unlocked()
            return len(b)

    def _flush_unlocked(self):
        self._checkClosed('flush of closed file')
        while self._write_buf:
            try:
                # ssl sockets only except 'bytes', not bytearrays
                # so perhaps we should conditionally wrap this for perf?
                n = self.raw.write(bytes(self._write_buf))
            except io.BlockingIOError as e:
                n = e.characters_written
            del self._write_buf[:n]


def MakeFile(sock, mode='r', bufsize=io.DEFAULT_BUFFER_SIZE):
    if 'r' in mode:
        return io.BufferedReader(socket.SocketIO(sock, mode), bufsize)
    else:
        return BufferedWriter(socket.SocketIO(sock, mode), bufsize)
