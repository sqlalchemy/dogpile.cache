import pprint
from unittest import TestCase
from dogpile.cache.api import CacheBackend, CachedValue, NO_VALUE
from dogpile.cache import make_region, register_backend, CacheRegion, util
from . import eq_, is_, assert_raises_message, io, configparser
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

    def test_instance_from_config_string(self):
        my_conf = \
            '[xyz]\n'\
            'cache.example.backend=mock\n'\
            'cache.example.expiration_time=600\n'\
            'cache.example.arguments.url=127.0.0.1\n'\
            'cache.example.arguments.dogpile_lockfile=false\n'\
            'cache.example.arguments.xyz=None\n'

        my_region = make_region()
        config = configparser.ConfigParser()
        config.readfp(io.StringIO(my_conf))

        my_region.configure_from_config(dict(config.items('xyz')), 'cache.example.')
        eq_(my_region.expiration_time, 600)
        assert isinstance(my_region.backend, MockBackend) is True
        eq_(my_region.backend.arguments, {'url': '127.0.0.1', 
                            'dogpile_lockfile':False, 'xyz':None})

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

    def test_dupe_config(self):
        reg = CacheRegion()
        reg.configure("mock")
        assert_raises_message(
            Exception,
            "This region is already configured",
            reg.configure, "mock"
        )

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
        eq_(reg.get("some key", expiration_time=10), NO_VALUE)
        reg.invalidate()
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
        time.sleep(2)
        is_(reg.get("some key"), NO_VALUE)
        eq_(reg.get("some key", ignore_expiration=True), "some value 1")
        eq_(reg.get_or_create("some key", creator), "some value 2")
        eq_(reg.get("some key"), "some value 2")

    def test_expire_on_get(self):
        reg = self._region(config_args={"expiration_time":.5})
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")
        time.sleep(1)
        is_(reg.get("some key"), NO_VALUE)

    def test_ignore_expire_on_get(self):
        reg = self._region(config_args={"expiration_time":.5})
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")
        time.sleep(1)
        eq_(reg.get("some key", ignore_expiration=True), "some value")

    def test_override_expire_on_get(self):
        reg = self._region(config_args={"expiration_time":.5})
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")
        time.sleep(1)
        eq_(reg.get("some key", expiration_time=5), "some value")
        is_(reg.get("some key"), NO_VALUE)

    def test_expire_override(self):
        reg = self._region(config_args={"expiration_time":5})
        counter = itertools.count(1)
        def creator():
            return "some value %d" % next(counter)
        eq_(reg.get_or_create("some key", creator, expiration_time=1), 
                    "some value 1")
        time.sleep(2)
        eq_(reg.get("some key"), "some value 1")
        eq_(reg.get_or_create("some key", creator, expiration_time=1), 
                    "some value 2")
        eq_(reg.get("some key"), "some value 2")


    def test_invalidate_get(self):
        reg = self._region()
        reg.set("some key", "some value")
        reg.invalidate()
        is_(reg.get("some key"), NO_VALUE)

    def test_invalidate_get_or_create(self):
        reg = self._region()
        counter = itertools.count(1)
        def creator():
            return "some value %d" % next(counter)
        eq_(reg.get_or_create("some key", creator), 
                    "some value 1")

        reg.invalidate()
        eq_(reg.get_or_create("some key", creator), 
                    "some value 2")

class CacheDecoratorTest(TestCase):
    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        reg.configure(backend, **config_args)
        return reg

    def test_cache_arg(self):
        reg = self._region()

        counter = itertools.count(1)

        @reg.cache_on_arguments()
        def generate(x, y):
            return next(counter) + x + y

        eq_(generate(1, 2), 4)
        eq_(generate(2, 1), 5)
        eq_(generate(1, 2), 4)
        generate.invalidate(1, 2)
        eq_(generate(1, 2), 6)
