import pprint
from unittest import TestCase
from dogpile.cache.api import CacheBackend, CachedValue, NO_VALUE
from dogpile.cache import make_region, register_backend, CacheRegion, util
from dogpile.cache.proxy import ProxyBackend
from . import eq_, is_, assert_raises_message, io, configparser
import time, datetime
import itertools
from collections import defaultdict
import operator

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
    def get_multi(self, keys):
        return [
            self.get(key) for key in keys
        ]

    def set(self, key, value):
        self._cache[key] = value
    def set_multi(self, mapping):
        for key,value in mapping.items():
            self.set(key, value)
    def delete(self, key):
        self._cache.pop(key, None)
    def delete_multi(self, keys):
        for key in keys:
            self.delete(key)
register_backend("mock", __name__, "MockBackend")

def key_mangler(key):
    return "HI!" + key

class RegionTest(TestCase):

    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        reg.configure(backend, **config_args)
        return reg

    def test_set_name(self):
        my_region = make_region(name='my-name')
        eq_(my_region.name, 'my-name')

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

    def test_datetime_expiration_time(self):
        my_region = make_region()
        my_region.configure(
            backend='mock',
            expiration_time=datetime.timedelta(days=1, hours=8)
        )
        eq_(my_region.expiration_time, 32*60*60)

    def test_reject_invalid_expiration_time(self):
        my_region = make_region()

        assert_raises_message(
            Exception,
            "expiration_time is not a number or timedelta.",
            my_region.configure, 'mock', 'one hour'
        )

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

    def test_multi_creator(self):
        reg = self._region()
        def creator(*keys):
            return ["some value %s" % key for key in keys]
        eq_(reg.get_or_create_multi(["k3", "k2", "k5"], creator),
                    ['some value k3', 'some value k2', 'some value k5'])

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

    def test_expire_multi(self):
        reg = self._region(config_args={"expiration_time":1})
        counter = itertools.count(1)
        def creator(*keys):
            return ["some value %s %d" % (key, next(counter)) for key in keys]
        eq_(reg.get_or_create_multi(["k3", "k2", "k5"], creator),
                    ['some value k3 2', 'some value k2 1', 'some value k5 3'])
        time.sleep(2)
        is_(reg.get("k2"), NO_VALUE)
        eq_(reg.get("k2", ignore_expiration=True), "some value k2 1")
        eq_(reg.get_or_create_multi(["k3", "k2"], creator),
                    ['some value k3 5', 'some value k2 4'])
        eq_(reg.get("k2"), "some value k2 4")

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

    def test_should_cache_fn(self):
        reg = self._region()
        values = [1, 2, 3]
        def creator():
            return values.pop(0)
        should_cache_fn = lambda val: val in (1, 3)
        ret = reg.get_or_create(
                    "some key", creator,
                    should_cache_fn=should_cache_fn)
        eq_(ret, 1)
        eq_(reg.backend._cache['some key'][0], 1)
        reg.invalidate()
        ret = reg.get_or_create(
                    "some key", creator,
                    should_cache_fn=should_cache_fn)
        eq_(ret, 2)
        eq_(reg.backend._cache['some key'][0], 1)
        reg.invalidate()
        ret = reg.get_or_create(
                    "some key", creator,
                    should_cache_fn=should_cache_fn)
        eq_(ret, 3)
        eq_(reg.backend._cache['some key'][0], 3)

    def test_should_cache_fn_multi(self):
        reg = self._region()
        values = [1, 2, 3]
        def creator(*keys):
            v = values.pop(0)
            return [v for k in keys]
        should_cache_fn = lambda val: val in (1, 3)
        ret = reg.get_or_create_multi(
                    [1, 2], creator,
                    should_cache_fn=should_cache_fn)
        eq_(ret, [1, 1])
        eq_(reg.backend._cache[1][0], 1)
        reg.invalidate()
        ret = reg.get_or_create_multi(
                    [1, 2], creator,
                    should_cache_fn=should_cache_fn)
        eq_(ret, [2, 2])
        eq_(reg.backend._cache[1][0], 1)
        reg.invalidate()
        ret = reg.get_or_create_multi(
                    [1, 2], creator,
                    should_cache_fn=should_cache_fn)
        eq_(ret, [3, 3])
        eq_(reg.backend._cache[1][0], 3)

    def test_should_set_multiple_values(self):
        reg = self._region()
        values = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        reg.set_multi(values)
        eq_(values['key1'], reg.get('key1'))
        eq_(values['key2'], reg.get('key2'))
        eq_(values['key3'], reg.get('key3'))

    def test_should_get_multiple_values(self):
        reg = self._region()
        values = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        reg.set_multi(values)
        reg_values = reg.get_multi(['key1', 'key2', 'key3'])
        eq_(
            reg_values,
            ["value1", "value2", "value3"]
        )

    def test_should_delete_multiple_values(self):
        reg = self._region()
        values = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        reg.set_multi(values)
        reg.delete_multi(['key2', 'key1000'])
        eq_(values['key1'], reg.get('key1'))
        eq_(NO_VALUE, reg.get('key2'))
        eq_(values['key3'], reg.get('key3'))


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

    def test_reentrant_call(self):
        reg = self._region(backend="dogpile.cache.memory")

        counter = itertools.count(1)

        # if these two classes get the same namespace,
        # you get a reentrant deadlock.
        class Foo(object):
            @classmethod
            @reg.cache_on_arguments(namespace="foo")
            def generate(cls, x, y):
                return next(counter) + x + y

        class Bar(object):
            @classmethod
            @reg.cache_on_arguments(namespace="bar")
            def generate(cls, x, y):
                return Foo.generate(x, y)

        eq_(Bar.generate(1, 2), 4)

    def test_multi(self):
        reg = self._region()

        counter = itertools.count(1)

        @reg.cache_multi_on_arguments()
        def generate(*args):
            return ["%d %d" % (arg, next(counter)) for arg in args]

        eq_(generate(2, 8, 10), ['2 2', '8 3', '10 1'])
        eq_(generate(2, 9, 10), ['2 2', '9 4', '10 1'])

        generate.invalidate(2)
        eq_(generate(2, 7, 10), ['2 5', '7 6', '10 1'])

        generate.set({7: 18, 10: 15})
        eq_(generate(2, 7, 10), ['2 5', 18, 15])

    def test_multi_asdict(self):
        reg = self._region()

        counter = itertools.count(1)

        @reg.cache_multi_on_arguments(asdict=True)
        def generate(*args):
            return dict(
                    [(arg, "%d %d" % (arg, next(counter))) for arg in args]
                    )

        eq_(generate(2, 8, 10), {2: '2 2', 8: '8 3', 10: '10 1'})
        eq_(generate(2, 9, 10), {2: '2 2', 9: '9 4', 10: '10 1'})

        generate.invalidate(2)
        eq_(generate(2, 7, 10), {2: '2 5', 7: '7 6', 10: '10 1'})

        generate.set({7: 18, 10: 15})
        eq_(generate(2, 7, 10), {2: '2 5', 7: 18, 10: 15})

    def test_multi_asdict_keys_missing(self):
        reg = self._region()

        counter = itertools.count(1)

        @reg.cache_multi_on_arguments(asdict=True)
        def generate(*args):
            return dict(
                    [(arg, "%d %d" % (arg, next(counter)))
                        for arg in args if arg != 10]
                    )

        eq_(generate(2, 8, 10), {2: '2 1', 8: '8 2'})
        eq_(generate(2, 9, 10), {2: '2 1', 9: '9 3'})

        assert reg.get(10) is NO_VALUE

        generate.invalidate(2)
        eq_(generate(2, 7, 10), {2: '2 4', 7: '7 5'})

        generate.set({7: 18, 10: 15})
        eq_(generate(2, 7, 10), {2: '2 4', 7: 18, 10: 15})

    def test_multi_asdict_keys_missing_existing_cache_fn(self):
        reg = self._region()

        counter = itertools.count(1)

        @reg.cache_multi_on_arguments(asdict=True,
                            should_cache_fn=lambda v: not v.startswith('8 '))
        def generate(*args):
            return dict(
                    [(arg, "%d %d" % (arg, next(counter)))
                        for arg in args if arg != 10]
                    )

        eq_(generate(2, 8, 10), {2: '2 1', 8: '8 2'})
        eq_(generate(2, 8, 10), {2: '2 1', 8: '8 3'})
        eq_(generate(2, 8, 10), {2: '2 1', 8: '8 4'})
        eq_(generate(2, 9, 10), {2: '2 1', 9: '9 5'})

        assert reg.get(10) is NO_VALUE

        generate.invalidate(2)
        eq_(generate(2, 7, 10), {2: '2 6', 7: '7 7'})

        generate.set({7: 18, 10: 15})
        eq_(generate(2, 7, 10), {2: '2 6', 7: 18, 10: 15})

    def test_multi_namespace(self):
        reg = self._region()

        counter = itertools.count(1)

        @reg.cache_multi_on_arguments(namespace="foo")
        def generate(*args):
            return ["%d %d" % (arg, next(counter)) for arg in args]

        eq_(generate(2, 8, 10), ['2 2', '8 3', '10 1'])
        eq_(generate(2, 9, 10), ['2 2', '9 4', '10 1'])

        eq_(
            sorted(list(reg.backend._cache)),
            [
            'tests.cache.test_region:generate|foo|10',
            'tests.cache.test_region:generate|foo|2',
            'tests.cache.test_region:generate|foo|8',
            'tests.cache.test_region:generate|foo|9']
        )
        generate.invalidate(2)
        eq_(generate(2, 7, 10), ['2 5', '7 6', '10 1'])

        generate.set({7: 18, 10: 15})
        eq_(generate(2, 7, 10), ['2 5', 18, 15])



class ProxyRegionTest(RegionTest):
    ''' This is exactly the same as the region test above, but it goes through
    a dummy proxy.  The purpose of this is to make sure the tests  still run
    successfully even when there is a proxy '''

    class MockProxy(ProxyBackend):

        @property
        def _cache(self):
            return self.proxied._cache


    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        config_args['wrap'] = [ProxyRegionTest.MockProxy]
        reg.configure(backend,  **config_args)
        return reg



class ProxyBackendTest(TestCase):

    class GetCounterProxy(ProxyBackend):
        counter = 0
        def get(self, key):
            ProxyBackendTest.GetCounterProxy.counter += 1
            return self.proxied.get(key)

    class SetCounterProxy(ProxyBackend):
        counter = 0
        def set(self, key, value):
            ProxyBackendTest.SetCounterProxy.counter += 1
            return self.proxied.set(key, value)

    class UsedKeysProxy(ProxyBackend):
        ''' Keep a counter of hose often we set a particular key'''

        def __init__(self, *args, **kwargs):
            super(ProxyBackendTest.UsedKeysProxy, self).__init__(
                                        *args, **kwargs)
            self._key_count = defaultdict(lambda: 0)

        def setcount(self, key):
            return self._key_count[key]

        def set(self, key, value):
            self._key_count[key] += 1
            self.proxied.set(key, value)

    class NeverSetProxy(ProxyBackend):
        ''' A totally contrived example of a Proxy that we pass arguments to.
        Never set a key that matches never_set '''

        def __init__(self, never_set, *args, **kwargs):
            super(ProxyBackendTest.NeverSetProxy, self).__init__(*args, **kwargs)
            self.never_set = never_set
            self._key_count = defaultdict(lambda: 0)

        def set(self, key, value):
            if key != self.never_set:
                self.proxied.set(key, value)


    def _region(self, init_args={}, config_args={}, backend="mock"):
        reg = CacheRegion(**init_args)
        reg.configure(backend, **config_args)
        return reg

    def test_counter_proxies(self):
        # count up the gets and sets and make sure they are passed through
        # to the backend properly.  Test that methods not overridden
        # continue to work

        reg = self._region(config_args={"wrap": [
            ProxyBackendTest.GetCounterProxy,
            ProxyBackendTest.SetCounterProxy]})
        ProxyBackendTest.GetCounterProxy.counter = 0
        ProxyBackendTest.SetCounterProxy.counter = 0

        # set a range of values in the cache
        for i in range(10):
            reg.set(i, i)
        eq_(ProxyBackendTest.GetCounterProxy.counter, 0)
        eq_(ProxyBackendTest.SetCounterProxy.counter, 10)

        # check that the range of values is still there
        for i in range(10):
            v = reg.get(i)
            eq_(v, i)
        eq_(ProxyBackendTest.GetCounterProxy.counter, 10)
        eq_(ProxyBackendTest.SetCounterProxy.counter, 10)

        # make sure the delete function(not overridden) still
        # executes properly
        for i in range(10):
            reg.delete(i)
            v = reg.get(i)
            is_(v, NO_VALUE)

    def test_instance_proxies(self):
        # Test that we can create an instance of a new proxy and
        # pass that to make_region instead of the class.  The two instances
        # should not interfere with each other
        proxy_num = ProxyBackendTest.UsedKeysProxy(5)
        proxy_abc = ProxyBackendTest.UsedKeysProxy(5)
        reg_num = self._region(config_args={"wrap": [proxy_num]})
        reg_abc = self._region(config_args={"wrap": [proxy_abc]})
        for i in range(10):
            reg_num.set(i, True)
            reg_abc.set(chr(ord('a') + i), True)

        for i in range(5):
            reg_num.set(i, True)
            reg_abc.set(chr(ord('a') + i), True)

        # make sure proxy_num has the right counts per key
        eq_(proxy_num.setcount(1), 2)
        eq_(proxy_num.setcount(9), 1)
        eq_(proxy_num.setcount('a'), 0)

        # make sure proxy_abc has the right counts per key
        eq_(proxy_abc.setcount('a'), 2)
        eq_(proxy_abc.setcount('g'), 1)
        eq_(proxy_abc.setcount('9'), 0)

    def test_argument_proxies(self):
        # Test that we can pass an argument to Proxy on creation
        proxy = ProxyBackendTest.NeverSetProxy(5)
        reg = self._region(config_args={"wrap": [proxy]})
        for i in range(10):
            reg.set(i, True)

        # make sure 1 was set, but 5 was not
        eq_(reg.get(5), NO_VALUE)
        eq_(reg.get(1), True)

