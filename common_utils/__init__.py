import functools
import threading

RESOURCE_REQUESTS_ADMINS_INFO = {
    'rkc7h',
    'kc2bj',
    'cyj7aj',
    'nem2p',
    'cyj7aj',
    'jf2dg',
    'clm8v',
    'jus2yw',
    'khs3z'
}
RESOURCE_REQUESTS_SERVICE_UNITS_TIERS = ['ssz_standard', 'ssz_instructional', 'ssz_paid', 'hsz_standard', 'hsz_paid']
RESOURCE_REQUESTS_STORAGE_TIERS = ['ssz_standard', 'ssz_project', 'hsz_standard', 'hsz_project']
RESOURCE_REQUESTS_STATUS_TYPES = ['pending', 'processing', 'active', 'expired', 'retiring', 'retired', 'error']
RESOURCE_TYPES = ['hpc_service_units', 'storage']
RESOURCE_REQUEST_FREE_SERVICE_UNITS_SSZ_STANDARD = 1000000


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