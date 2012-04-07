"""Provides backends for talking to memcached."""

from dogpile.cache.api import CacheBackend, CachedValue, NO_VALUE
from dogpile.cache import util

class PylibmcBackend(CacheBackend):
    """A backend for the `pylibmc <http://sendapatch.se/projects/pylibmc/index.html>`_ 
    memcached client.
    
    E.g.::
    
        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.pylibmc',
            expiration_time = 3600,
            arguments = {
                'url':["127.0.0.1"],
                'binary':True,
                'behaviors':{"tcp_nodelay": True,"ketama":True}
            }
        )
    
    Arguments which can be passed to the ``arguments`` 
    dictionary include:
    
    :param url: the string URL to connect to.  Can be a single
     string or a list of strings.
    :param binary: sets the ``binary`` flag understood by
     ``pylibmc.Client``.
    :param behaviors: a dictionary which will be passed to
     ``pylibmc.Client`` as the ``behaviors`` parameter.
    :param memcached_expire_time: integer, when present will
     be passed as the ``time`` parameter to ``pylibmc.Client.set``.
     This is used to set the memcached expiry time for a value.
     
     Note that this is **different** from Dogpile's own 
     ``expiration_time``, which is the number of seconds after
     which Dogpile will consider the value to be expired, however
     Dogpile **will continue to use this value** until a new
     one can be generated, when using :meth:`.CacheRegion.get_or_create`.
     Therefore, if you are setting ``memcached_expire_time``, you'll
     usually want to make sure it is greater than ``expiration_time`` 
     by at least enough seconds for new values to be generated.
    :param min_compres_len: Integer, will be passed as the 
     ``min_compress_len`` parameter to the ``pylibmc.Client.set``
     method.
     
    Threading
    ---------
    
    The :class:`.PylibmcBackend` uses a ``threading.local()``
    object to store individual ``pylibmc.Client`` objects per thread.
    ``threading.local()`` has the advantage over pylibmc's built-in
    thread pool in that it automatically discards objects associated
    with a particular thread when that thread ends.
    
    """

    def __init__(self, arguments):
        self._imports()
        self.url = util.to_list(arguments['url'])
        self.binary = arguments.get('binary', False)
        self.behaviors = arguments.get('behaviors', {})
        self.memcached_expire_time = arguments.get(
                                        'memcached_expire_time', 0)
        self.min_compress_len = arguments.get('min_compress_len', 0)

        self._pylibmc_set_args = {}
        if "memcached_expire_time" in arguments:
            self._pylibmc_set_args["time"] = \
                            arguments["memcached_expire_time"]
        if "min_compress_len" in arguments:
            self._pylibmc_set_args["min_compress_len"] = \
                            arguments["min_compress_len"]
        backend = self

        # using a plain threading.local here.   threading.local
        # automatically deletes the __dict__ when a thread ends,
        # so the idea is that this is superior to pylibmc's
        # own ThreadMappedPool which doesn't handle this 
        # automatically.
        class ClientPool(util.threading.local):
            def __init__(self):
                self.memcached = backend._create_client()

        self._clients = ClientPool()

    def _imports(self):
        global pylibmc
        import pylibmc

    def _create_client(self):
        return pylibmc.Client(self.url, 
                        binary=self.binary,
                        behaviors=self.behaviors
                    )

    def get(self, key):
        value = self._clients.memcached.get(key)
        if value is None:
            return NO_VALUE
        else:
            return value

    def set(self, key, value):
        self._clients.memcached.set(
                                    key, 
                                    value, 
                                    **self._pylibmc_set_args
                                )

    def delete(self, key):
        self._clients.memcached.delete(key)
