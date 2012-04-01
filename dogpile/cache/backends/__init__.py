from dogpile.cache.region import register_backend

register_backend("dbm", "dogpile.cache.backends.dbm", "DBMBackend")
register_backend("pylibmc", "dogpile.cache.backends.memcached", "PylibmcBackend")
register_backend("memory", "dogpile.cache.backends.memory", "MemoryBackend")
