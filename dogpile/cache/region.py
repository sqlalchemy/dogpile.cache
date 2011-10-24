import inspect


_backend_loader = PluginLoader("dogpile.cache")
register_backend = _backend_loader.register
import backends

class CacheRegion(object):
    """A front end to a particular cache backend."""

    def __init__(self, name, 
            expiration_time=None,
            arguments=None,
            function_key_generator=_function_key_generator
            key_mangler=None,
        ):
        self.backend = _backend_loadeer.load(name)(arguents)
        self.function_key_generator = function_key_genertor
        self.key_mangler = key_mangler
        self.dogpile = Dogpile(expiration_time, init=True)

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
        dogpile = 
        with dogpile.acquire(gen_cached, get_value) as value:
            return value

    def _dogpile_get_value(self):
        value = 
             with mc_pool.reserve() as mc:
                value = mc.get(key)
                if value is None:
                    raise NeedRegenerationException()
                return value

    import pylibmc
    mc_pool = pylibmc.ThreadMappedPool(pylibmc.Client("localhost"))

    from dogpile import Dogpile, NeedRegenerationException

    def cached(key, expiration_time):
        """A decorator that will cache the return value of a function
        in memcached given a key."""

        def get_value():
             with mc_pool.reserve() as mc:
                value = mc.get(key)
                if value is None:
                    raise NeedRegenerationException()
                return value

        dogpile = Dogpile(expiration_time, init=True)

        def decorate(fn):
            def gen_cached():
                value = fn()
                with mc_pool.reserve() as mc:
                    mc.put(key, value)
                return value

            def invoke():
                with dogpile.acquire(gen_cached, get_value) as value:
                    return value
            return invoke

        return decorate



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

         The generation of the key from the function is the big controversial
        thing that was a source of user issues with Beaker. Dogpile provides
        the latest and greatest algorithm used by Beaker, but also allows you
        to use whatever function you want, by specifying it to
        ``make_region()`` using the ``function_key_generator`` argument. 
        """


make_region = CacheRegion


