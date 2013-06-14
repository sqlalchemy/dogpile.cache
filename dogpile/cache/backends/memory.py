"""
Memory Backend
--------------

Provides a simple dictionary-based backend.

"""

from dogpile.cache.api import CacheBackend, NO_VALUE

class MemoryBackend(CacheBackend):
    """A backend that uses a plain dictionary.

    There is no size management, and values which
    are placed into the dictionary will remain
    until explicitly removed.   Note that
    Dogpile's expiration of items is based on
    timestamps and does not remove them from
    the cache.

    E.g.::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.memory'
        )


    To use a Python dictionary of your choosing,
    it can be passed in with the ``cache_dict``
    argument::

        my_dictionary = {}
        region = make_region().configure(
            'dogpile.cache.memory',
            arguments={
                "cache_dict":my_dictionary
            }
        )


    """
    def __init__(self, arguments):
        self._cache = arguments.pop("cache_dict", {})

    def get(self, key):
        return self._cache.get(key, NO_VALUE)

    def get_multi(self, keys):
        return [
            self._cache.get(key, NO_VALUE)
            for key in keys
        ]

    def set(self, key, value):
        self._cache[key] = value

    def set_multi(self, mapping):
        for key,value in mapping.items():
            self._cache[key] = value

    def delete(self, key):
        self._cache.pop(key, None)

    def delete_multi(self, keys):
        for key in keys:
            self._cache.pop(key, None)
