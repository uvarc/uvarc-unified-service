import functools
import threading


def synchronized(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        try:
            _ = self._lock
        except AttributeError:
            self._lock = threading.Lock()

        with self._lock:
            return f(self, *args, **kwargs)
    return wrapper