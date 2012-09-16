from dogpile.core import Dogpile, NeedRegenerationException
from dogpile.core.nameregistry import NameRegistry

from .util import function_key_generator, PluginLoader, \
    memoized_property, coerce_string_conf
from .api import NO_VALUE, CachedValue
import time
from functools import wraps

_backend_loader = PluginLoader("dogpile.cache")
register_backend = _backend_loader.register
from . import backends

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

        def my_key_generator(namespace, fn):
            fname = fn.__name__
            def generate_key(*arg):
                return namespace + "_" + fname + "_".join(str(s) for s in arg)
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

     The ``namespace`` is that passed to
     :meth:`.CacheRegion.cache_on_arguments`.  It's not consulted
     outside this function, so in fact can be of any form.
     For example, it can be passed as a tuple, used to specify
     arguments to pluck from \**kw::

        def my_key_generator(namespace, fn):
            def generate_key(*arg, **kw):
                return ":".join(
                        [kw[k] for k in namespace] +
                        [str(x) for x in arg]
                    )

     Where the decorator might be used as::

        @my_region.cache_on_arguments(namespace=('x', 'y'))
        def my_function(a, b, **kw):
            return my_data()

    :param key_mangler: Function which will be used on all incoming
     keys before passing to the backend.  Defaults to ``None``,
     in which case the key mangling function recommended by
     the cache backend will be used.    A typical mangler
     is the SHA1 mangler found at :func:`.sha1_mangle_key`
     which coerces keys into a SHA1
     hash, so that the string length is fixed.  To
     disable all key mangling, set to ``False``.

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
        self._invalidated = None

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
         decorator (though note:  **not** the :meth:`.CacheRegion.get`
         method) will call upon the value creation function after this
         time period has passed since the last generation.

         .. note::

            The expiration_time is only stored *locally*,
            within the :class:`.CacheRegion` instance, and not
            in the cache itself.  Only the *creation time* of a
            particular value is stored along with it in the cache.
            This means an individual :class:`.CacheRegion` can
            be modified to have a different expiration time, which
            will have an immediate effect on data in the cache without
            the need to set new values.


        :param arguments:   Optional.  The structure here is passed
         directly to the constructor of the :class:`.CacheBackend`
         in use, though is typically a dictionary.

        """
        if "backend" in self.__dict__:
            raise Exception(
                    "This region is already "
                    "configured with backend: %s"
                    % self.backend)
        backend_cls = _backend_loader.load(backend)
        if _config_argument_dict:
            self.backend = backend_cls.from_config_dict(
                _config_argument_dict,
                _config_prefix
            )
        else:
            self.backend = backend_cls(arguments or {})
        self.expiration_time = expiration_time
        self.dogpile_registry = NameRegistry(self._create_dogpile)
        if self.key_mangler is None:
            self.key_mangler = self.backend.key_mangler
        return self

    def _create_dogpile(self, identifier, expiration_time):
        if expiration_time is None:
            expiration_time = self.expiration_time
        return Dogpile(
                expiration_time,
                lock=self.backend.get_mutex(identifier)
            )

    def invalidate(self):
        """Invalidate this :class:`.CacheRegion`.

        Invalidation works by setting a current timestamp
        (using ``time.time()``)
        representing the "minimum creation time" for
        a value.  Any retrieved value whose creation
        time is prior to this timestamp
        is considered to be stale.  It does not
        affect the data in the cache in any way, and is also
        local to this instance of :class:`.CacheRegion`.

        Once set, the invalidation time is honored by
        the :meth:`.CacheRegion.get_or_create` and
        :meth:`.CacheRegion.get` methods.

        .. versionadded:: 0.3.0

        """
        self._invalidated = time.time()

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
            memcached_region.configure_from_config(myconfig,
                                                "cache.memcached.")

        """
        config_dict = coerce_string_conf(config_dict)
        return self.configure(
            config_dict["%sbackend" % prefix],
            expiration_time = config_dict.get(
                                "%sexpiration_time" % prefix, None),
            _config_argument_dict=config_dict,
            _config_prefix="%sarguments." % prefix
        )

    @memoized_property
    def backend(self):
        raise Exception("No backend is configured on this region.")

    def get(self, key, expiration_time=None, ignore_expiration=False):
        """Return a value from the cache, based on the given key.

        If the value is not present, the method returns the token
        ``NO_VALUE``. ``NO_VALUE`` evaluates to False, but is separate from
        ``None`` to distinguish between a cached value of ``None``.

        By default, the configured expiration time of the
        :class:`.CacheRegion`, or alternatively the expiration
        time supplied by the ``expiration_time`` argument,
        is tested against the creation time of the retrieved
        value versus the current time (as reported by ``time.time()``).
        If stale, the cached value is ignored and the ``NO_VALUE``
        token is returned.  Passing the flag ``ignore_expiration=True``
        bypasses the expiration time check.

        .. versionchanged:: 0.3.0
           :meth:`.CacheRegion.get` now checks the value's creation time
           against the expiration time, rather than returning
           the value unconditionally.

        The method also interprets the cached value in terms
        of the current "invalidation" time as set by
        the :meth:`.invalidate` method.   If a value is present,
        but its creation time is older than the current
        invalidation time, the ``NO_VALUE`` token is returned.
        Passing the flag ``ignore_expiration=True`` bypasses
        the invalidation time check.

        .. versionadded:: 0.3.0
           Support for the :meth:`.CacheRegion.invalidate`
           method.

        :param key: Key to be retrieved. While it's typical for a key to be a
         string, it is ultimately passed directly down to the cache backend,
         before being optionally processed by the key_mangler function, so can
         be of any type recognized by the backend or by the key_mangler
         function, if present.

        :param expiration_time: Optional expiration time value
         which will supersede that configured on the :class:`.CacheRegion`
         itself.

         .. versionadded:: 0.3.0

        :param ignore_expiration: if ``True``, the value is returned
         from the cache if present, regardless of configured
         expiration times or whether or not :meth:`.invalidate`
         was called.

         .. versionadded:: 0.3.0

        """

        if self.key_mangler:
            key = self.key_mangler(key)
        value = self.backend.get(key)
        if value is NO_VALUE:
            return value
        elif not ignore_expiration:
            if expiration_time is None:
                expiration_time = self.expiration_time
            if expiration_time is not None and \
                time.time() - value.metadata["ct"] > expiration_time:
                return NO_VALUE
            elif self._invalidated and value.metadata["ct"] < self._invalidated:
                return NO_VALUE

        return value.payload

    def get_or_create(self, key, creator, expiration_time=None):
        """Return a cached value based on the given key.

        If the value does not exist or is considered to be expired
        based on its creation time, the given
        creation function may or may not be used to recreate the value
        and persist the newly generated value in the cache.

        Whether or not the function is used depends on if the
        *dogpile lock* can be acquired or not.  If it can't, it means
        a different thread or process is already running a creation
        function for this key against the cache.  When the dogpile
        lock cannot be acquired, the method will block if no
        previous value is available, until the lock is released and
        a new value available.  If a previous value
        is available, that value is returned immediately without blocking.

        If the :meth:`.invalidate` method has been called, and
        the retrieved value's timestamp is older than the invalidation
        timestamp, the value is unconditionally prevented from
        being returned.  The method will attempt to acquire the dogpile
        lock to generate a new value, or will wait
        until the lock is released to return the new value.

        .. versionchanged:: 0.3.0
          The value is unconditionally regenerated if the creation
          time is older than the last call to :meth:`.invalidate`.

        :param key: Key to be retrieved. While it's typical for a key to be a
         string, it is ultimately passed directly down to the cache backend,
         before being optionally processed by the key_mangler function, so can
         be of any type recognized by the backend or by the key_mangler
         function, if present.

        :param creator: function which creates a new value.
        :param expiration_time: optional expiration time which will overide
         the expiration time already configured on this :class:`.CacheRegion`
         if not None.   To set no expiration, use the value -1.

         .. note::

            the expiration_time argument here is **not guaranteed** to be
            effective if multiple concurrent threads are accessing the same
            key via :meth:`get_or_create` using different values
            for ``expiration_time`` - the first thread within a cluster
            of concurrent usages establishes the expiration time within a
            :class:`.Dogpile` instance for the duration of those usages.
            It is advised that all access to a particular key within a particular
            :class:`.CacheRegion` use the **same** value for ``expiration_time``.
            Sticking with the default expiration time configured for
            the :class:`.CacheRegion` as a whole is expected to be the
            usual mode of operation.

        See also:

        :meth:`.CacheRegion.cache_on_arguments` - applies :meth:`.get_or_create`
        to any function using a decorator.

        """
        if self.key_mangler:
            key = self.key_mangler(key)

        def get_value():
            value = self.backend.get(key)
            if value is NO_VALUE or \
                value.metadata['v'] != value_version or \
                    (self._invalidated and
                    value.metadata["ct"] < self._invalidated):
                raise NeedRegenerationException()
            return value.payload, value.metadata["ct"]

        def gen_value():
            value = self._value(creator())
            self.backend.set(key, value)
            return value.payload, value.metadata["ct"]

        dogpile = self.dogpile_registry.get(key, expiration_time)
        with dogpile.acquire(gen_value,
                    value_and_created_fn=get_value) as value:
            return value

    def _value(self, value):
        """Return a :class:`.CachedValue` given a value."""
        return CachedValue(value, {
                            "ct":time.time(),
                            "v":value_version
                        })

    def set(self, key, value):
        """Place a new value in the cache under the given key."""

        if self.key_mangler:
            key = self.key_mangler(key)
        self.backend.set(key, self._value(value))


    def delete(self, key):
        """Remove a value from the cache.

        This operation is idempotent (can be called multiple times, or on a
        non-existent key, safely)
        """

        if self.key_mangler:
            key = self.key_mangler(key)

        self.backend.delete(key)

    def cache_on_arguments(self, namespace=None, expiration_time=None):
        """A function decorator that will cache the return
        value of the function using a key derived from the
        function itself and its arguments.

        The decorator internally makes use of the
        :meth:`.CacheRegion.get_or_create` method to access the
        cache and conditionally call the function.  See that
        method for additional behavioral details.

        E.g.::

            @someregion.cache_on_arguments()
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

        The default key generation will use the name
        of the function, the module name for the function,
        the arguments passed, as well as an optional "namespace"
        parameter in order to generate a cache key.

        Given a function ``one`` inside the module
        ``myapp.tools``::

            @region.cache_on_arguments(namespace="foo")
            def one(a, b):
                return a + b

        Above, calling ``one(3, 4)`` will produce a
        cache key as follows::

            myapp.tools:one|foo|3, 4

        The key generator will ignore an initial argument
        of ``self`` or ``cls``, making the decorator suitable
        (with caveats) for use with instance or class methods.
        Given the example::

            class MyClass(object):
                @region.cache_on_arguments(namespace="foo")
                def one(self, a, b):
                    return a + b

        The cache key above for ``MyClass().one(3, 4)`` will
        again produce the same cache key of ``myapp.tools:one|foo|3, 4`` -
        the name ``self`` is skipped.

        The ``namespace`` parameter is optional, and is used
        normally to disambiguate two functions of the same
        name within the same module, as can occur when decorating
        instance or class methods as below::

            class MyClass(object):
                @region.cache_on_arguments(namespace='MC')
                def somemethod(self, x, y):
                    ""

            class MyOtherClass(object):
                @region.cache_on_arguments(namespace='MOC')
                def somemethod(self, x, y):
                    ""

        Above, the ``namespace`` parameter disambiguates
        between ``somemethod`` on ``MyClass`` and ``MyOtherClass``.
        Python class declaration mechanics otherwise prevent
        the decorator from having awareness of the ``MyClass``
        and ``MyOtherClass`` names, as the function is received
        by the decorator before it becomes an instance method.

        The function key generation can be entirely replaced
        on a per-region basis using the ``function_key_generator``
        argument present on :func:`.make_region` and
        :class:`.CacheRegion`. If defaults to
        :func:`.function_key_generator`.

        :param namespace: optional string argument which will be
         established as part of the cache key.   This may be needed
         to disambiguate functions of the same name within the same
         source file, such as those
         associated with classes - note that the decorator itself
         can't see the parent class on a function as the class is
         being declared.
        :param expiration_time: if not None, will override the normal
         expiration time.
        """
        def decorator(fn):
            key_generator = self.function_key_generator(namespace, fn)
            @wraps(fn)
            def decorate(*arg, **kw):
                key = key_generator(*arg, **kw)
                def creator():
                    return fn(*arg, **kw)
                return self.get_or_create(key, creator, expiration_time)

            def invalidate(*arg, **kw):
                key = key_generator(*arg, **kw)
                self.delete(key)

            decorate.invalidate = invalidate

            return decorate
        return decorator

def make_region(*arg, **kw):
    """Instantiate a new :class:`.CacheRegion`.

    Currently, :func:`.make_region` is a passthrough
    to :class:`.CacheRegion`.  See that class for
    constructor arguments.

    """
    return CacheRegion(*arg, **kw)

