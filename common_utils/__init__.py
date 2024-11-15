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


def cors_check(app, origin):
    abort_flag = True
    if origin:
        for allowed_url in app.config['CORS_ENABLED_ALLOWED_ORIGINS']:
            if allowed_url in origin:
                abort_flag = False
    return abort_flag