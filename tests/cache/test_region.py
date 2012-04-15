from unittest import TestCase
from dogpile.cache.api import CacheBackend, CachedValue, NO_VALUE
from dogpile.cache import make_region, register_backend, CacheRegion
from . import eq_, assert_raises_message
import time
import itertools

class MockMutex(object):
    def __init__(self, key):
        self.key = key
    def acquire(self, blocking=True):
        return True
    def release(self):
        return

class MockBackend(CacheBackend):
    def __init__(self, arguments):
        self.arguments = arguments
        self._cache = {}
    def get_mutex(self, key):
        return MockMutex(key)
    def get(self, key):
        try:
            return self._cache[key]
        except KeyError:
            return NO_VALUE
    def set(self, key, value):
        self._cache[key] = value
    def delete(self, key):
        self._cache.pop(key, None)
register_backend("mock", __name__, "MockBackend")

def key_mangler(key):
    return "HI!" + key

class RegionTest(TestCase):

    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        reg.configure(backend, **config_args)
        return reg

    def test_instance_from_dict(self):
        my_conf = { 
            'cache.example.backend': 'mock',
            'cache.example.expiration_time': 600,
            'cache.example.arguments.url': '127.0.0.1'
            } 
        my_region = make_region()
        my_region.configure_from_config(my_conf, 'cache.example.')
        eq_(my_region.expiration_time, 600)
        assert isinstance(my_region.backend, MockBackend) is True
        eq_(my_region.backend.arguments, {'url': '127.0.0.1'})

    def test_key_mangler_argument(self):
        reg = self._region(init_args={"key_mangler":key_mangler})
        assert reg.key_mangler is key_mangler

        reg = self._region()
        assert reg.key_mangler is None

        MockBackend.key_mangler = km = lambda self, k: "foo"
        reg = self._region()
        eq_(reg.key_mangler("bar"), "foo")
        MockBackend.key_mangler = None

    def test_key_mangler_impl(self):
        reg = self._region(init_args={"key_mangler":key_mangler})

        reg.set("some key", "some value")
        eq_(list(reg.backend._cache), ["HI!some key"])
        eq_(reg.get("some key"), "some value")
        eq_(reg.get_or_create("some key", lambda: "some new value"), "some value")
        reg.delete("some key")
        eq_(reg.get("some key"), NO_VALUE)

    def test_no_config(self):
        reg = CacheRegion()
        assert_raises_message(
            Exception,
            "No backend is configured on this region.",
            getattr, reg, "backend"
        )

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

    def test_expire_override(self):
        reg = self._region(config_args={"expiration_time":5})
        counter = itertools.count(1)
        def creator():
            return "some value %d" % next(counter)
        eq_(reg.get_or_create("some key", creator, expiration_time=1), 
                    "some value 1")
        time.sleep(1)
        eq_(reg.get("some key"), "some value 1")
        eq_(reg.get_or_create("some key", creator, expiration_time=1), 
                    "some value 2")
        eq_(reg.get("some key"), "some value 2")

