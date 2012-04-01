from unittest import TestCase
from dogpile.cache.api import CacheBackend, CachedValue, NO_VALUE
from dogpile.cache import register_backend, CacheRegion
from tests import eq_, assert_raises_message
import time
import itertools

class MemoryBackendTest(TestCase):

    def _region(self, init_args={}, config_args={}, backend="dogpile.cache.memory"):
        reg = CacheRegion(**init_args)
        reg.configure(backend, **config_args)
        return reg

    def test_set_get_value(self):
        reg = self._region()
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")

    def test_set_get_nothing(self):
        reg = self._region()
        eq_(reg.get("some key"), NO_VALUE)

    def test_creator(self):
        reg = self._region()
        def creator():
            return "some value"
        eq_(reg.get_or_create("some key", creator), "some value")

    def test_remove(self):
        reg = self._region()
        reg.set("some key", "some value")
        reg.delete("some key")
        reg.delete("some key")
        eq_(reg.get("some key"), NO_VALUE)

    def test_expire(self):
        reg = self._region(config_args={"expiration_time":1})
        counter = itertools.count(1)
        def creator():
            return "some value %d" % next(counter)
        eq_(reg.get_or_create("some key", creator), "some value 1")
        time.sleep(1)
        eq_(reg.get("some key"), "some value 1")
        eq_(reg.get_or_create("some key", creator), "some value 2")
        eq_(reg.get("some key"), "some value 2")

