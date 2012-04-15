from ._fixtures import _GenericBackendFixture
from . import eq_
from unittest import TestCase
import time
from dogpile.cache import util
import inspect

class DecoratorTest(_GenericBackendFixture, TestCase):
    backend = "dogpile.cache.memory"

    def _fixture(self, namespace=None, expiration_time=None):
        reg = self._region(config_args={"expiration_time":.25})

        counter = [0]
        @reg.cache_on_arguments(namespace=namespace, 
                            expiration_time=expiration_time)
        def go(a, b):
            counter[0] +=1
            return counter[0], a, b
        return go

    def test_decorator(self):
        go = self._fixture()
        eq_(go(1, 2), (1, 1, 2))
        eq_(go(3, 4), (2, 3, 4))
        eq_(go(1, 2), (1, 1, 2))
        time.sleep(.3)
        eq_(go(1, 2), (3, 1, 2))

    def test_decorator_namespace(self):
        # TODO: test the namespace actually
        # working somehow...
        go = self._fixture(namespace="x")
        eq_(go(1, 2), (1, 1, 2))
        eq_(go(3, 4), (2, 3, 4))
        eq_(go(1, 2), (1, 1, 2))
        time.sleep(.3)
        eq_(go(1, 2), (3, 1, 2))

    def test_decorator_custom_expire(self):
        go = self._fixture(expiration_time=.5)
        eq_(go(1, 2), (1, 1, 2))
        eq_(go(3, 4), (2, 3, 4))
        eq_(go(1, 2), (1, 1, 2))
        time.sleep(.3)
        eq_(go(1, 2), (1, 1, 2))
        time.sleep(.3)
        eq_(go(1, 2), (3, 1, 2))

    def test_explicit_expire(self):
        go = self._fixture(expiration_time=1)
        eq_(go(1, 2), (1, 1, 2))
        eq_(go(3, 4), (2, 3, 4))
        eq_(go(1, 2), (1, 1, 2))
        go.invalidate(1, 2)
        eq_(go(1, 2), (3, 1, 2))

class KeyGenerationTest(TestCase):
    def _keygen_decorator(self, namespace=None):
        canary = []
        def decorate(fn):
            canary.append(util.function_key_generator(namespace, fn))
            return fn
        return decorate, canary

    def test_keygen_fn(self):
        decorate, canary = self._keygen_decorator()

        @decorate
        def one(a, b):
            pass
        gen = canary[0]

        eq_(gen(1, 2), "tests.cache.test_decorator:one|1 2")
        eq_(gen(None, 5), "tests.cache.test_decorator:one|None 5")

    def test_keygen_fn_namespace(self):
        decorate, canary = self._keygen_decorator("mynamespace")

        @decorate
        def one(a, b):
            pass
        gen = canary[0]

        eq_(gen(1, 2), "tests.cache.test_decorator:one|mynamespace|1 2")
        eq_(gen(None, 5), "tests.cache.test_decorator:one|mynamespace|None 5")


