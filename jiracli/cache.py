"""

"""
from contextlib import closing
from functools import wraps
import hashlib
import os
import pickle
import shutil
import time
from jiracli.utils import CONFIG_DIR

CACHE_DIR = os.path.join(CONFIG_DIR, 'cache')
CACHE_DURATION = 60*60*24

def cached(name):
    def __inner(fn):
        @wraps(fn)
        def _inner(*args, **kwargs):
            token = hashlib.md5(
                "".join([str(k) for k in args] + [str(k) for k in kwargs.values()]).encode('utf-8')
            ).hexdigest()
            cached = CachedData(name + token)
            if not cached.get():
                resp = fn(*args, **kwargs)
                cached.update(resp)
            return cached.get()
        return _inner
    return __inner


class CachedData(object):
    def __init__(self, name):
        self.name = name
        self.cached = None
        self.path = os.path.join(CACHE_DIR, self.name + '.cache')
        if not os.path.isdir(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def update(self, data):
        with closing(open(self.path, 'wb')) as fp:
            self.cached = data
            fp.write(pickle.dumps(data))

    def invalidate(self):
        if os.path.isfile(self.path):
            os.unlink(self.path)
        self.cached = None

    def get(self):
        try:
            with closing(open(self.path, 'rb')) as fp:
                if (time.time() - os.stat(self.path).st_mtime) >= CACHE_DURATION:
                    self.invalidate()
                else:
                    self.cached = pickle.loads(fp.read())
        except AttributeError:
            self.invalidate()
        except IOError:
            return None
        finally:
            return self.cached


def clear_cache(*cached_data):
    if not cached_data:
        if os.path.isdir(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
    else:
        for data in cached_data:
            data.invalidate()
