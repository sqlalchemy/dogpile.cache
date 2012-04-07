from dogpile.cache.api import CacheBackend, CachedValue, NO_VALUE
from dogpile.cache import register_backend, CacheRegion
from tests import eq_, assert_raises_message
import itertools
import time
from nose import SkipTest

from unittest import TestCase

class _GenericBackendTest(TestCase):
    @classmethod
    def setup_class(cls):
        try:
            cls._region()
        except ImportError:
            raise SkipTest("Backend %s not installed" % cls.backend)

    backend = None
    region_args = {}
    config_args = {}

    @classmethod
    def _region(cls, region_args={}, config_args={}):
        _region_args = {}
        _region_args = cls.region_args.copy()
        _region_args.update(**region_args)
        reg = CacheRegion(**_region_args)
        _config_args = cls.config_args.copy()
        _config_args.update(config_args)
        reg.configure(cls.backend, **_config_args)
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
