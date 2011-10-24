from dogpile.cache.region import register_backend

register_backend("dbm", "dogpile.cache.backends.dbm", "DbmBackend")
register_backend("pylibmc", "dogpile.cache.backends.memcached", "PylibmcBackend")
