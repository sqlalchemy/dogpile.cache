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

VALKEY_HOST = "127.0.0.1"
VALKEY_PORT = int(os.getenv("DOGPILE_VALKEY_PORT", "6379"))
expect_valkey_running = os.getenv("DOGPILE_VALKEY_PORT") is not None


class _TestValkeyConn:
    @classmethod
    def _check_backend_available(cls, backend):
        try:
            backend.set_serialized("x", b"y")
            assert backend.get_serialized("x") == b"y"
            backend.delete("x")
        except Exception:
            if not expect_valkey_running:
                pytest.skip(
                    "valkey is not running or "
                    "otherwise not functioning correctly"
                )
            else:
                raise


class ValkeyTest(_TestValkeyConn, _GenericBackendTestSuite):
    backend = "dogpile.cache.valkey"
    config_args = {
        "arguments": {
            "host": VALKEY_HOST,
            "port": VALKEY_PORT,
            "db": 0,
            "foo": "barf",
        }
    }


class ValkeySerializerTest(_GenericSerializerTestSuite, ValkeyTest):
    pass


class ValkeyDistributedMutexTest(_TestValkeyConn, _GenericMutexTestSuite):
    backend = "dogpile.cache.valkey"
    config_args = {
        "arguments": {
            "host": VALKEY_HOST,
            "port": VALKEY_PORT,
            "db": 0,
            "distributed_lock": True,
        }
    }


class ValkeyAsyncCreationTest(_TestValkeyConn, _GenericBackendFixture):
    backend = "dogpile.cache.valkey"
    config_args = {
        "arguments": {
            "host": VALKEY_HOST,
            "port": VALKEY_PORT,
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


@patch("valkey.StrictValkey", autospec=True)
class ValkeyConnectionTest:
    backend = "dogpile.cache.valkey"

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

    def test_connect_with_defaults(self, MockStrictValkey):
        # The defaults, used if keys are missing from the arguments dict.
        arguments = {
            "host": "localhost",
            "port": 6379,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictValkey, expected, arguments)

    def test_connect_with_basics(self, MockStrictValkey):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictValkey, expected, arguments)

    def test_connect_with_password(self, MockStrictValkey):
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
        self._test_helper(MockStrictValkey, expected, arguments)

    def test_connect_with_username_and_password(self, MockStrictValkey):
        arguments = {
            "host": "127.0.0.1",
            "username": "valkey",
            "password": "some password",
            "port": 6379,
            "db": 0,
        }
        self._test_helper(MockStrictValkey, arguments)

    def test_connect_with_socket_timeout(self, MockStrictValkey):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "socket_timeout": 0.5,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictValkey, expected, arguments)

    def test_connect_with_socket_connect_timeout(self, MockStrictValkey):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "socket_timeout": 1.0,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictValkey, expected, arguments)

    def test_connect_with_socket_keepalive(self, MockStrictValkey):
        arguments = {
            "host": "127.0.0.1",
            "port": 6379,
            "socket_keepalive": True,
            "db": 0,
        }
        expected = arguments.copy()
        expected.update({"username": None, "password": None})
        self._test_helper(MockStrictValkey, expected, arguments)

    def test_connect_with_socket_keepalive_options(self, MockStrictValkey):
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
        self._test_helper(MockStrictValkey, expected, arguments)

    def test_connect_with_connection_pool(self, MockStrictValkey):
        pool = Mock()
        arguments = {"connection_pool": pool, "socket_timeout": 0.5}
        expected_args = {"connection_pool": pool}
        self._test_helper(
            MockStrictValkey, expected_args, connection_args=arguments
        )

    def test_connect_with_url(self, MockStrictValkey):
        arguments = {"url": "valkey://valkey:password@127.0.0.1:6379/0"}
        self._test_helper(MockStrictValkey.from_url, arguments)

    def test_extra_arbitrary_args(self, MockStrictValkey):
        arguments = {
            "url": "valkey://valkey:password@127.0.0.1:6379/0",
            "connection_kwargs": {
                "ssl": True,
                "encoding": "utf-8",
                "new_valkey_arg": 50,
            },
        }
        self._test_helper(
            MockStrictValkey.from_url,
            {
                "url": "valkey://valkey:password@127.0.0.1:6379/0",
                "ssl": True,
                "encoding": "utf-8",
                "new_valkey_arg": 50,
            },
            arguments,
        )
