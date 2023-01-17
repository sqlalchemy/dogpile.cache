import json
from unittest import TestCase

from dogpile.cache.api import NO_VALUE
from ._fixtures import _GenericBackendFixture
from ._fixtures import _GenericBackendTest
from ._fixtures import _GenericSerializerTest
from . import eq_


class MemoryBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory"


class MemoryBackendSerializerTest(_GenericSerializerTest, MemoryBackendTest):
    pass


class MemoryBackendSerializerNoValueTest(_GenericBackendFixture, TestCase):
    backend = "dogpile.cache.memory"

    region_args = {
        "serializer": lambda v: json.dumps(v).encode("ascii"),
        "deserializer": lambda v: NO_VALUE,
    }

    def test_serializer_no_value(self):
        region = self._region()

        value = {"foo": ["bar", 1, False, None]}
        region.set("k", value)

        asserted = region.get("k")

        eq_(asserted, NO_VALUE)


class MemoryPickleBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory_pickle"
