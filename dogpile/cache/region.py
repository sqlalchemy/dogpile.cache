from dogpile import Dogpile, NeedRegenerationException
from dogpile.nameregistry import NameRegistry

from dogpile.cache.util import function_key_generator, PluginLoader, memoized_property
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
    """A front end to a particular cache backend.
    
    :param name: Optional, a string name for the region.
     This isn't used internally
     but can be accessed via the ``.name`` parameter, helpful
     for configuring a region from a config file.
    :param function_key_generator:  Optional.  A 
     function that will produce a "cache key" given 
     a data creation function and arguments, when using
     the :meth:`.CacheRegion.cache_on_arguments` method.
     The structure of this function
     should be two levels: given the data creation function, 
     return a new function that generates the key based on 
     the given arguments.  Such as::

        def my_key_generator(fn):
            namespace = fn.__name__
            def generate_key(*arg):
                return namespace + "_".join(str(s) for s in arg)
            return generate_key


        region = make_region(
            function_key_generator = my_key_generator
        ).configure(
            "dogpile.cache.dbm",
            expiration_time=300,
            arguments={
                "filename":"file.dbm"
            }
        )

    :param key_mangler: Function which will be used on all incoming
     keys before passing to the backend.  Defaults to ``None``,
     in which case the key mangling function recommended by
     the cache backend will be used.    A typical mangler
     is the SHA1 mangler found at found at :meth:`.sha1_mangle_key` 
     which coerces keys into a SHA1
     hash, so that the string length is fixed.  To
     disable all key mangling, set to ``False``.
    :param lock_generator: Function which, given a cache key,
     returns a mutexing object.
    
    """

    def __init__(self,
            name=None, 
            function_key_generator=function_key_generator,
            key_mangler=None

    ):
        """Construct a new :class:`.CacheRegion`."""
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
        """Configure a :class:`.CacheRegion`.
        
        The :class:`.CacheRegion` itself 
        is returned.
        
        :param backend:   Required.  This is the name of the 
         :class:`.CacheBackend` to use, and is resolved by loading 
         the class from the ``dogpile.cache`` entrypoint.

        :param expiration_time:   Optional.  The expiration time passed 
         to the dogpile system.  The :meth:`.CacheRegion.get_or_create`
         method as well as the :meth:`.CacheRegion.cache_on_arguments` 
         decorator (though note:  **not** the :meth:`.CacheRegion.get` method)
         will call upon the value creation function after this
         time period has passed since the last generation.

        :param arguments:   Optional.  The structure here is passed directly 
         to the constructor of the :class:`.CacheBackend` in use, though 
         is typically a dictionary.
         
        """
        if "backend" in self.__dict__:
            raise Exception(
                    "This region is already "
                    "configured with the %s backend" 
                    % self.backend)
        backend_cls = _backend_loader.load(backend)
        if _config_argument_dict:
            self.backend = backend_cls.from_config_dict(
                _config_argument_dict,
                _config_prefix
            )
        else:
            self.backend = backend_cls(arguments)
        self.expiration_time = expiration_time
        self.dogpile_registry = NameRegistry(self._create_dogpile)
        if self.key_mangler is None:
            self.key_mangler = self.backend.key_mangler
        return self

    def _create_dogpile(self, identifier):
        return Dogpile(
                self.expiration_time, 
                lock=self.backend.get_mutex(identifier)
            )

    def configure_from_config(self, config_dict, prefix):
        """Configure from a configuration dictionary 
        and a prefix.
        
        Example::
        
            local_region = make_region()
            memcached_region = make_region()

            # regions are ready to use for function
            # decorators, but not yet for actual caching

            # later, when config is available
            myconfig = {
                "cache.local.backend":"dogpile.cache.dbm",
                "cache.local.arguments.filename":"/path/to/dbmfile.dbm",
                "cache.memcached.backend":"dogpile.cache.pylibmc",
                "cache.memcached.arguments.url":"127.0.0.1, 10.0.0.1",
            }
            local_region.configure_from_config(myconfig, "cache.local.")
            memcached_region.configure_from_config(myconfig, "cache.memcached.")

        """
        return self.configure(
            config_dict["%s.backend" % prefix],
            expiration_time = config_dict.get("%s.expiration_time" % prefix, None),
            _config_argument_dict=config_dict,
            _config_prefix="%s.arguments" % prefix
        )

    @memoized_property
    def backend(self):
        raise Exception("No backend is configured on this region.")

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
            value = self._value(creator())
            self.backend.put(key, value)
            return value

        dogpile = self.dogpile_registry.get(key)
        with dogpile.acquire(gen_value, value_and_created_fn=get_value) as value:
            return value

    def _value(self, value):
        """Return a :class:`.CachedValue` given a value."""
        return CachedValue(value, {
                            "creation_time":time.time(), 
                            "version":value_version
                        })

    def put(self, key, value):
        """Place a new value in the cache under the given key."""

        if self.key_mangler:
            key = self.key_mangler(key)
        self.backend.put(key, self._value(value))


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

        The generation of the key from the function is the big 
        controversial thing that was a source of user issues with Beaker.  Dogpile
        provides the latest and greatest algorithm used by Beaker, but also
        allows you to use whatever function you want, by specifying it
        to using the ``function_key_generator`` argument to :func:`.make_region`
        and/or :class:`.CacheRegion`.  If defaults to :func:`.function_key_generator`.

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

def make_region(*arg, **kw):
    """Instantiate a new :class:`.CacheRegion`.
    
    Currently, :func:`.make_region` is a passthrough
    to :class:`.CacheRegion`.  See that class for
    constructor arguments.
    
    """
    return CacheRegion(*arg, **kw)

