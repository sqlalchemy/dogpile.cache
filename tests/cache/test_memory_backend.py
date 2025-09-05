from dogpile.testing.fixtures import _GenericBackendTestSuite
from dogpile.testing.fixtures import _GenericSerializerTestSuite


class MemoryBackendTest(_GenericBackendTestSuite):
    backend = "dogpile.cache.memory"
    backend_argument_names = ["cache_dict"]


class MemoryBackendSerializerTest(
    _GenericSerializerTestSuite, MemoryBackendTest
):
    pass


class MemoryPickleBackendTest(MemoryBackendTest):
    backend = "dogpile.cache.memory_pickle"
