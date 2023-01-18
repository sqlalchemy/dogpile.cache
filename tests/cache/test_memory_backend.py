import json
from unittest import TestCase

from dogpile.cache.api import CantDeserializeException
from dogpile.cache.api import NO_VALUE
from . import eq_
from ._fixtures import _GenericBackendFixture
from ._fixtures import _GenericBackendTest
from ._fixtures import _GenericSerializerTest


class MemoryBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory"


class MemoryBackendSerializerTest(_GenericSerializerTest, MemoryBackendTest):
    pass


def raise_cant_deserialize_exception(v):
    raise CantDeserializeException()


class MemoryBackendSerializerCantDeserializeExceptionTest(
    _GenericBackendFixture, TestCase
):
    backend = "dogpile.cache.memory"

    region_args = {
        "serializer": lambda v: json.dumps(v).encode("ascii"),
        "deserializer": raise_cant_deserialize_exception,
    }

    def test_serializer_cant_deserialize(self):
        region = self._region()

        value = {"foo": ["bar", 1, False, None]}
        region.set("k", value)

        asserted = region.get("k")

        eq_(asserted, NO_VALUE)


class MemoryPickleBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory_pickle"
