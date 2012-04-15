from ._fixtures import _GenericBackendTest

class MemoryBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory"

