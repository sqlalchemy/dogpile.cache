from dogpile.testing.fixtures import _GenericBackendTestSuite
from dogpile.testing.fixtures import _GenericSerializerTestSuite


class MemoryBackendTest(_GenericBackendTestSuite):
    backend = "dogpile.cache.memory"
    config_args = {"arguments": {"cache_dict": {}}}

    def test_config_args_does_not_mutate(self):
        assert "cache_dict" in self.config_args["arguments"]


class MemoryBackendSerializerTest(
    _GenericSerializerTestSuite, MemoryBackendTest
):
    pass


class MemoryPickleBackendTest(MemoryBackendTest):
    backend = "dogpile.cache.memory_pickle"
