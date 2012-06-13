from dogpile.cache.api import CacheBackend, CachedValue, NO_VALUE
from dogpile.cache import register_backend, CacheRegion, util
from dogpile.cache.region import _backend_loader
from . import eq_, assert_raises_message
import itertools
import time
from nose import SkipTest
from threading import Thread, Lock
from unittest import TestCase

class _GenericBackendFixture(object):
    @classmethod
    def setup_class(cls):
        try:
            backend_cls = _backend_loader.load(cls.backend)
            backend = backend_cls(cls.config_args.get('arguments', {}))
        except ImportError:
            raise SkipTest("Backend %s not installed" % cls.backend)
        cls._check_backend_available(backend)

    @classmethod
    def _check_backend_available(cls, backend):
        pass

    region_args = {}
    config_args = {}

    _region_inst = None
    _backend_inst = None

    def _region(self, region_args={}, config_args={}):
        _region_args = self.region_args.copy()
        _region_args.update(**region_args)
        _config_args = self.config_args.copy()
        _config_args.update(config_args)

        self._region_inst = reg = CacheRegion(**_region_args)
        reg.configure(self.backend, **_config_args)
        return reg

    def _backend(self):
        backend_cls = _backend_loader.load(self.backend)
        _config_args = self.config_args.copy()
        self._backend_inst = backend_cls(_config_args.get('arguments', {}))
        return self._backend_inst

class _GenericBackendTest(_GenericBackendFixture, TestCase):
    def tearDown(self):
        if self._region_inst:
            self._region_inst.delete("some key")
        elif self._backend_inst:
            self._backend_inst.delete("some_key")

    def test_backend_get_nothing(self):
        backend = self._backend()
        eq_(backend.get("some_key"), NO_VALUE)

    def test_backend_delete_nothing(self):
        backend = self._backend()
        backend.delete("some_key")

    def test_backend_set_get_value(self):
        backend = self._backend()
        backend.set("some_key", "some value")
        eq_(backend.get("some_key"), "some value")

    def test_backend_delete(self):
        backend = self._backend()
        backend.set("some_key", "some value")
        backend.delete("some_key")
        eq_(backend.get("some_key"), NO_VALUE)

    def test_region_set_get_value(self):
        reg = self._region()
        reg.set("some key", "some value")
        eq_(reg.get("some key"), "some value")

    def test_region_set_get_nothing(self):
        reg = self._region()
        eq_(reg.get("some key"), NO_VALUE)

    def test_region_creator(self):
        reg = self._region()
        def creator():
            return "some value"
        eq_(reg.get_or_create("some key", creator), "some value")

    def test_threaded_dogpile(self):
        # run a basic dogpile concurrency test.
        # note the concurrency of dogpile itself
        # is intensively tested as part of dogpile.
        reg = self._region(config_args={"expiration_time":.25})
        lock = Lock()
        canary = []
        def creator():
            ack = lock.acquire(False)
            canary.append(ack)
            time.sleep(.5)
            if ack:
                lock.release()
            return "some value"
        def f():
            for x in range(5):
                reg.get_or_create("some key", creator)
                time.sleep(.5)

        threads = [Thread(target=f) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(canary) > 3
        assert False not in canary

    def test_region_delete(self):
        reg = self._region()
        reg.set("some key", "some value")
        reg.delete("some key")
        reg.delete("some key")
        eq_(reg.get("some key"), NO_VALUE)

    def test_region_expire(self):
        reg = self._region(config_args={"expiration_time":.25})
        counter = itertools.count(1)
        def creator():
            return "some value %d" % next(counter)
        eq_(reg.get_or_create("some key", creator), "some value 1")
        time.sleep(.4)
        eq_(reg.get("some key", ignore_expiration=True), "some value 1")
        eq_(reg.get_or_create("some key", creator), "some value 2")
        eq_(reg.get("some key"), "some value 2")

class _GenericMutexTest(_GenericBackendFixture, TestCase):
    def test_mutex(self):
        backend = self._backend()
        mutex = backend.get_mutex("foo")

        ac = mutex.acquire()
        assert ac
        ac2 = mutex.acquire(wait=False)
        assert not ac2
        mutex.release()
        ac3 = mutex.acquire()
        assert ac3
        mutex.release()

    def test_mutex_threaded(self):
        backend = self._backend()
        mutex = backend.get_mutex("foo")

        lock = Lock()
        canary = []
        def f():
            for x in range(5):
                mutex = backend.get_mutex("foo")
                mutex.acquire()
                for y in range(5):
                    ack = lock.acquire(False)
                    canary.append(ack)
                    time.sleep(.002)
                    if ack:
                        lock.release()
                mutex.release()
                time.sleep(.02)

        threads = [Thread(target=f) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert False not in canary

    def test_mutex_reentrant_across_keys(self):
        backend = self._backend()
        for x in range(3):
            m1 = backend.get_mutex("foo")
            m2 = backend.get_mutex("bar")
            try:
                m1.acquire()
                assert m2.acquire(wait=False)
                assert not m2.acquire(wait=False)
                m2.release()

                assert m2.acquire(wait=False)
                assert not m2.acquire(wait=False)
                m2.release()
            finally:
                m1.release()

    def test_reentrant_dogpile(self):
        reg = self._region()
        def create_foo():
            return "foo" + reg.get_or_create("bar", create_bar)

        def create_bar():
            return "bar"

        eq_(
            reg.get_or_create("foo", create_foo),
            "foobar"
        )
        eq_(
            reg.get_or_create("foo", create_foo),
            "foobar"
        )
