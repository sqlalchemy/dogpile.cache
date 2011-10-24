from dogpile import Dogpile, NeedRegenerationException
from dogpile.cache.util import function_key_generator, PluginLoader
from dogpile.cache.api import NO_VALUE, CachedValue
import time

_backend_loader = PluginLoader("dogpile.cache")
register_backend = _backend_loader.register
import backends

value_version = 1
"""An integer placed in the :class:`.CachedValue`
so that new versions of dogpile.cache can detect cached
values from a previous, backwards-incompatible version.

"""

class CacheRegion(object):
    """A front end to a particular cache backend."""

    def __init__(self,
            name=None, 
            function_key_generator=function_key_generator,
            key_mangler=None,

    ):
        """Construct a new :class:`.CacheRegion`.
        
        :param name: Optional, name for the region.
        :function_key_generator: Optional, key generator used by
         :meth:`.CacheRegion.cache_on_arguments`.
        :key_mangler: Function which will be used on all incoming
         keys before passing to the backend.  Defaults to ``None``,
         in which case the key mangling function recommended by
         the cache backend will be used.    A typical mangler
         is the SHA1 mangler found at found at :meth:`.sha1_mangle_key` 
         which coerces keys into a SHA1
         hash, so that the string length is fixed.  To
         disable all key mangling, set to ``False``.
        
        """
        self.function_key_generator = function_key_generator
        if key_mangler:
            self.key_mangler = key_mangler
        else:
            self.key_mangler = None

    def configure(self, backend,
            expiration_time=None,
            arguments=None,
            _config_argument_dict=None,
            _config_prefix=None
        ):
        """Configure a :class:`.CacheRegion`
        
        The :class:`.CacheRegion` itself 
        is returned..
        
        :param backend: Cache backend name
        :param expiration_time: Expiration time, in seconds
        :param arguments: Argument structure passed to the 
         backend.  Is typically a dict.
         
        """
        backend_cls = _backend_loader.load(backend)
        if _config_argument_dict:
            self.backend = backend_cls.from_config_dict(
                _config_argument_dict,
                _config_prefix
            )
        else:
            self.backend = backend_cls(arguments)
        self.dogpile_registry = Dogpile.registry(expiration_time)
        if self.key_mangler is None:
            self.key_mangler = backend.key_mangler
        return self

    def configure_from_config(self, config_dict, prefix):
        """Configure from a configuration dictionary 
        and a prefix."""
        return self.configure(
            config_dict["%s.backend" % prefix],
            expiration_time = config_dict.get("%s.expiration_time" % prefix, None),
            _config_argument_dict=config_dict,
            _config_prefix="%s.arguments" % prefix
        )

    def get(self, key):
        """Return a value from the cache, based on the given key.

        While it's typical the key is a string, it's passed through to the
        underlying backend so can be of any type recognized by the backend. If
        the value is not present, returns the token ``NO_VALUE``. ``NO_VALUE``
        evaluates to False, but is separate from ``None`` to distinguish
        between a cached value of ``None``. Note that the ``expiration_time``
        argument is **not** used here - this method is a direct line to the
        backend's behavior. 

        """

        if self.key_mangler:
            key = self.key_mangler(key)
        value = self.backend.get(key)
        return value.payload

    def get_or_create(self, key, creator):
        """Similar to ``get``, will use the given "creation" function to create a new
        value if the value does not exist.

        This will use the underlying dogpile/
        expiration mechanism to determine when/how the creation function is called.

        """
        if self.key_mangler:
            key = self.key_mangler(key)

        def get_value():
            value = self.backend.get(key)
            if value is NO_VALUE or \
                value.metadata['version'] != value_version:
                raise NeedRegenerationException()
            return value.payload, value.metadata["creation_time"]

        def gen_value():
            value = CachedValue(
                        creator(), 
                        {
                            "creation_time":time.time(), 
                            "version":value_version
                        })
            self.backend.put(key, value)
            return value

        dogpile = self.dogpile_registry.get(key)
        with dogpile.acquire(gen_value, value_and_created_fn=get_value) as value:
            return value

    def put(self, key, value):
        """Place a new value in the cache under the given key."""

        if self.key_mangler:
            key = self.key_mangler(key)
        self.backend.put(key, CachedValue(value))


    def delete(self, key):
        """Remove a value from the cache.

        This operation is idempotent (can be called multiple times, or on a 
        non-existent key, safely)
        """

        if self.key_mangler:
            key = self.key_mangler(key)

        self.backend.delete(key)

    def cache_on_arguments(self, fn):
        """A function decorator that will cache the return value of the
        function using a key derived from the name of the function, its
        location within the application (i.e. source filename) as well as the
        arguments passed to the function.
        
        E.g.::
        
            @someregion.cache_on_arguments
            def generate_something(x, y):
                return somedatabase.query(x, y)
                
        The decorated function can then be called normally, where
        data will be pulled from the cache region unless a new
        value is needed::
        
            result = generate_something(5, 6)
        
        The function is also given an attribute ``invalidate``, which
        provides for invalidation of the value.  Pass to ``invalidate()``
        the same arguments you'd pass to the function itself to represent
        a particular value::
        
            generate_something.invalidate(5, 6)
        
        The mechanism used to generate cache keys is controlled
        by the ``function_key_generator`` function passed
        to :class:`.CacheRegion`. It defaults to :func:`.function_key_generator`.    

        """
        key_generator = self.function_key_generator(fn)
        def decorate(*arg, **kw):
            key = key_generator(*arg, **kw)
            def creator():
                return fn(*arg, **kw)
            return self.get_or_create(key, creator)

        def invalidate(*arg, **kw):
            key = key_generator(*arg, **kw)
            self.delete(key)

        decorate.invalidate = invalidate

        return decorate

make_region = CacheRegion


