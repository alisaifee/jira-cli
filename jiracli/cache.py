"""

"""
from contextlib import closing
from functools import wraps
import hashlib
import os
import pickle
import time
from jiracli.utils import CONFIG_DIR

CACHE_DIR = os.path.join(CONFIG_DIR, 'cache')

def cached(name):
    def __inner(fn):
        @wraps(fn)
        def _inner(*args, **kwargs):
            token = hashlib.md5(
                "".join([str(k) for k in args] + [str(k) for k in kwargs.values()])
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
        with closing(open(self.path, 'w')) as fp:
            self.cached = data
            fp.write(pickle.dumps(data))

    def get(self):
        try:
            with closing(open(self.path)) as fp:
                if time.time() - os.stat(self.path).st_mtime > 60*60*24:
                    os.unlink(self.path)
                else:
                    self.cached = pickle.loads(fp.read())
        except AttributeError:
            if os.path.isfile(self.path):
                os.unlink(self.path)
        except IOError:
            return None
        finally:
            return self.cached