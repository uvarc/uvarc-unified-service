import functools
import threading

RESOURCE_REQUESTS_SERVICE_UNITS_TIERS = ['ssz_standard', 'ssz_instructional', 'ssz_paid', 'hsz_standard', 'hsz_paid']
RESOURCE_REQUESTS_STORAGE_TIERS = ['pending', 'processing', 'active', 'expired','error'] 


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