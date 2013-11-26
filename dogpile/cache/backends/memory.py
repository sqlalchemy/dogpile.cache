"""
Memory Backend
--------------

Provides a simple dictionary-based backend.

"""

from dogpile.cache.api import CacheBackend, NO_VALUE

try:
    import cPickle as pickle
except ImportError:
    import pickle

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
    is_pickle = False

    def __init__(self, arguments):
        self._cache = arguments.pop("cache_dict", {})

    def get(self, key):
        value = self._cache.get(key, NO_VALUE)
        if value is not NO_VALUE :
            if self.is_pickle :
                value = pickle.loads(value)
        return value 

    def get_multi(self, keys):
        values = []
        for key in keys :
            values.append(self.get(key))
        return values

    def set(self, key, value):
        if self.is_pickle :
            value = pickle.dumps(value)
        self._cache[key] = value

    def set_multi(self, mapping):
        for key,value in mapping.items():
            self.set(key, value)

    def delete(self, key):
        self._cache.pop(key, None)

    def delete_multi(self, keys):
        for key in keys:
            self._cache.pop(key, None)


class MemoryPickleBackend(MemoryBackend):
    """A backend that uses a plain dictionary, but serializes objects on `set` 
    and deserializes the objects on `get`.  This is because objects cached in 
    the MemoryBackend are cached as the actual object, so changes to them will
    persist without a `set`.  
    
    This backend takes a lightweight performance hit  through pickling, in order 
    to achieve parity with other cache backends where the objects returned by 
    `get` are a discretely new object, and `set` must be called to persist 
    changes.
    
    MemoryPickleBackend will try to serialize with cPickle, and will fall back 
    to pickle if it is not available.
    """
    is_pickle = True
