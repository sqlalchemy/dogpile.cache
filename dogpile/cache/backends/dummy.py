"""
Dummy Backend
-------------

The dummy backend does not do any cachingn at all. It is inteded to be used
to test behaviour without caching.
"""

from dogpile.cache.api import CacheBackend, NO_VALUE


__all__ = ['DummyBackend']


class DummyLock(object):  # pragma NO COVERAGE
    def acquire(self):
        pass

    def release(self):
        pass


class DummyBackend(CacheBackend):  # pragma NO COVERAGE
    def __init__(self, arguments):
        pass

    def get_mutex(self, key):
        return DummyLock()

    def get(self, key):
        return NO_VALUE

    def get_multiple(self, keys):
        return [NO_VALUE for k in keys]

    def set(self, key, value):
        pass

    def set_multiple(self, mapping):
        pass

    def delete(self, key):
        pass

    def delete_multiple(self, keys):
        pass
