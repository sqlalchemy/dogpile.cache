from dogpile.cache.region import register_backend

register_backend("dogpile.cache.dbm", "dogpile.cache.backends.dbm", "DBMBackend")
register_backend("dogpile.cache.pylibmc", "dogpile.cache.backends.memcached", "PylibmcBackend")
register_backend("dogpile.cache.memory", "dogpile.cache.backends.memory", "MemoryBackend")
