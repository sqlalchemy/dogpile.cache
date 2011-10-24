import operator

class NoValue(object):
    """Describe a missing cache value.
    
    The :attr:`.NO_VALUE` module global
    should be used.
    
    """
    @property
    def payload(self):
        return self

    def __nonzero__(self):
        return False

NO_VALUE = NoValue()
"""Value returned from ``get()`` that describes 
a  key not present."""

class CachedValue(tuple):
    """Represent a value stored in the cache.
    
    :class:.`CachedValue` is a two-tuple of
    ``(payload, metadata)``, where ``metadata``
    is dogpile.cache's tracking information (
    currently the creation time).  The metadata
    and tuple structure is pickleable, if 
    the backend requires serialization.
    
    """
    payload = operator.itemgetter(0)
    metadata = operator.itemgetter(1)

    def __new__(cls, payload, metadata):
        return tuple.__new__(cls, (payload, metadata))

class CacheBackend(object):
    """Base class for backend implementations."""

    def __init__(self, arguments):
        """Construct a new :class:`.CacheBackend`.
        
        Subclasses should override this to
        handle the given arguments.
        
        :param arguments: The ``arguments`` parameter
         passed to :func:`.make_registry`.
         
        """
        raise NotImplementedError()

    def get(self, key):
        """Retrieve a value from the cache.
        
        The returned value should be an instance of
        :class:`.CachedValue`, or ``NO_VALUE`` if
        not present.
        
        """
        raise NotImplementedError()

    def put(self, key, value):
        """Put a value in the cache.
        
        The key will be whatever was passed
        to the registry, processed by the
        "key mangling" function, if any.
        The value will always be an instance
        of :class:`.CachedValue`.
        
        """
        raise NotImplementedError()

    def delete(self, key):
        """Delete a value from the cache.
        
        The key will be whatever was passed
        to the registry, processed by the
        "key mangling" function, if any.
        
        The behavior here should be idempotent,
        that is, can be called any number of times
        regardless of whether or not the
        key exists.
        """
        raise NotImplementedError()
