from ._fixtures import _GenericBackendTest
from ._fixtures import _GenericSerializerTest


class MemoryBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory"


class MemoryBackendSerializerTest(_GenericSerializerTest, MemoryBackendTest):
    pass


class MemoryPickleBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory_pickle"
