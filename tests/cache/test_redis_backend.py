from concurrent.futures import ThreadPoolExecutor
import os
from threading import Event
import time
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from dogpile.cache.region import _backend_loader
from dogpile.testing import eq_
from dogpile.testing.fixtures import _GenericBackendFixture
from dogpile.testing.fixtures import _GenericBackendTestSuite
from dogpile.testing.fixtures import _GenericMutexTestSuite
from dogpile.testing.fixtures import _GenericSerializerTestSuite

REDIS_HOST = "127.0.0.1"
REDIS_PORT = int(os.getenv("DOGPILE_REDIS_PORT", "6379"))
expect_redis_running = os.getenv("DOGPILE_REDIS_PORT") is not None


class _TestRedisConn:
    @classmethod
    def _check_backend_available(cls, backend):
        try:
            backend.set_serialized("x", b"y")
            assert backend.get_serialized("x") == b"y"
            backend.delete("x")
        except Exception:
            if not expect_redis_running:
                pytest.skip(
                    "redis is not running or "
                    "otherwise not functioning correctly"
                )
            else:
                raise


class RedisTest(_TestRedisConn, _GenericBackendTestSuite):
    backend = "dogpile.cache.redis"
    config_args = {
        "arguments": {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": 0,
            "foo": "barf",
        }
    }


class RedisSerializerTest(_GenericSerializerTestSuite, RedisTest):
    pass


class RedisDistributedMutexTest(_TestRedisConn, _GenericMutexTestSuite):
    backend = "dogpile.cache.redis"
    config_args = {
        "arguments": {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": 0,
            "distributed_lock": True,
        }
    }


class RedisAsyncCreationTest(_TestRedisConn, _GenericBackendFixture):
    backend = "dogpile.cache.redis"
    config_args = {
        "arguments": {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": 0,
            "distributed_lock": True,
            # This is the important bit:
            "thread_local_lock": False,
        }
    }

    def test_distributed_async_locks(self):
        pool = ThreadPoolExecutor(max_workers=1)
        ev = Event()

        # A simple example of how people may implement an async runner -
        # plugged into a thread pool executor.
        def asyncer(cache, key, creator, mutex):
            def _call():
                try:
                    value = creator()
                    cache.set(key, value)
                finally:
                    # If a thread-local lock is used here, this will fail
                    # because generally the async calls run in a different
                    # thread (that's the point of async creators).
                    try:
                        mutex.release()
                    except Exception:
                        pass
                    else:
                        ev.set()

            return pool.submit(_call)

        reg = self._region(
            region_args={"async_creation_runner": asyncer},
            config_args={"expiration_time": 0.1},
        )

        @reg.cache_on_arguments()
        def blah(k):
            return k * 2

        # First call adds to the cache without calling the async creator.
        eq_(blah("asd"), "asdasd")

        # Wait long enough to cause the cached value to get stale.
        time.sleep(0.3)

        # This will trigger the async runner and return the stale value.
        eq_(blah("asd"), "asdasd")

        # Wait for the the async runner to finish or timeout. If the mutex
        # release errored, then the event won't be set and we'll timeout.
        # On <= Python 3.1, wait returned nothing. So check is_set after.
        ev.wait(timeout=1.0)
        eq_(ev.is_set(), True)


@patch("redis.StrictRedis", autospec=True)
class RedisConnectionTest:
    backend = "dogpile.cache.redis"

    @classmethod
    def setup_class(cls):
        cls.backend_cls = _backend_loader.load(cls.backend)
        try:
            cls.backend_cls({})
        except ImportError:
            pytest.skip("Backend %s not installed" % cls.backend)

    def _test_helper(self, mock_obj, expected_args, connection_args=None):
        if connection_args is None:
            connection_args = expected_args

        self.backend_cls(connection_args)
        mock_obj.assert_called_once_with(**expected_args)

    def test_connect_with_defaults(self, MockStrictRedis):
        # The defaults, used if keys are missing from the arguments dict.
        arguments = {
            "host": "localhost",
            "port": 6379,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictRedis, expected, arguments)

    def test_connect_with_basics(self, MockStrictRedis):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictRedis, expected, arguments)

    def test_connect_with_password(self, MockStrictRedis):
        arguments = {
            "host": "127.0.0.1",
            "password": "some password",
            "port": 6379,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update(
            {
                "username": None,
            }
        )
        self._test_helper(MockStrictRedis, expected, arguments)

    def test_connect_with_username_and_password(self, MockStrictRedis):
        arguments = {
            "host": "127.0.0.1",
            "username": "redis",
            "password": "some password",
            "port": 6379,
            "db": 0,
        }
        self._test_helper(MockStrictRedis, arguments)

    def test_connect_with_socket_timeout(self, MockStrictRedis):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "socket_timeout": 0.5,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictRedis, expected, arguments)

    def test_connect_with_socket_connect_timeout(self, MockStrictRedis):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "socket_timeout": 1.0,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictRedis, expected, arguments)

    def test_connect_with_socket_keepalive(self, MockStrictRedis):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "socket_keepalive": True,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictRedis, expected, arguments)

    def test_connect_with_socket_keepalive_options(self, MockStrictRedis):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "socket_keepalive": True,
            # 4 = socket.TCP_KEEPIDLE
            "socket_keepalive_options": {4, 10.0},
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictRedis, expected, arguments)

    def test_connect_with_connection_pool(self, MockStrictRedis):
        pool = Mock()
        arguments = {"connection_pool": pool, "socket_timeout": 0.5}
        expected_args = {"connection_pool": pool}
        self._test_helper(
            MockStrictRedis, expected_args, connection_args=arguments
        )

    def test_connect_with_url(self, MockStrictRedis):
        arguments = {"url": "redis://redis:password@127.0.0.1:6379/0"}
        self._test_helper(MockStrictRedis.from_url, arguments)

    def test_extra_arbitrary_args(self, MockStrictRedis):
        arguments = {
            "url": "redis://redis:password@127.0.0.1:6379/0",
            "connection_kwargs": {
                "ssl": True,
                "encoding": "utf-8",
                "new_redis_arg": 50,
            },
        }
        self._test_helper(
            MockStrictRedis.from_url,
            {
                "url": "redis://redis:password@127.0.0.1:6379/0",
                "ssl": True,
                "encoding": "utf-8",
                "new_redis_arg": 50,
            },
            arguments,
        )
