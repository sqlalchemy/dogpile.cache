from dogpile.cache.api import CacheBackend, CachedValue, NO_VALUE

class MemoryBackend(CacheBackend):
    def __init__(self, the_cache=None):
        if the_cache is None:
            self._cache = {}
        else:
            self._cache = the_cache

    def get(self, key):
        return self._cache.get(key, NO_VALUE)

    def set(self, key, value):
        self._cache[key] = value

    def delete(self, key):
        self._cache.pop(key, None)

