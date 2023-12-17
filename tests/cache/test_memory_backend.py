from dogpile.testing.fixtures import _GenericBackendTestSuite
from dogpile.testing.fixtures import _GenericSerializerTestSuite


class MemoryBackendTest(_GenericBackendTestSuite):
    backend = "dogpile.cache.memory"


class MemoryBackendSerializerTest(
    _GenericSerializerTestSuite, MemoryBackendTest
):
    pass


class MemoryPickleBackendTest(_GenericBackendTestSuite):
    backend = "dogpile.cache.memory_pickle"
