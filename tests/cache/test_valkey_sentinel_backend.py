from concurrent.futures import ThreadPoolExecutor
import os
from threading import Event
import time

from dogpile.testing import eq_
from dogpile.testing.fixtures import _GenericBackendFixture
from dogpile.testing.fixtures import _GenericBackendTestSuite
from dogpile.testing.fixtures import _GenericMutexTestSuite
from dogpile.testing.fixtures import _GenericSerializerTestSuite
from .test_valkey_backend import _TestValkeyConn as _TestValkeySentinelConn

VALKEY_HOST = "127.0.0.1"
VALKEY_PORT = int(os.getenv("DOGPILE_VALKEY_SENTINEL_PORT", "26379"))
expect_valkey_running = os.getenv("DOGPILE_VALKEY_SENTINEL_PORT") is not None


class ValkeySentinelTest(_TestValkeySentinelConn, _GenericBackendTestSuite):
    backend = "dogpile.cache.valkey_sentinel"
    config_args = {
        "arguments": {
            "sentinels": [[VALKEY_HOST, VALKEY_PORT]],
            "service_name": "pifpaf",
            "db": 0,
            "distributed_lock": False,
        }
    }


class ValkeySerializerTest(_GenericSerializerTestSuite, ValkeySentinelTest):
    pass


class ValkeySentinelDistributedMutexTest(
    _TestValkeySentinelConn, _GenericMutexTestSuite
):
    backend = "dogpile.cache.valkey_sentinel"
    config_args = {
        "arguments": {
            "sentinels": [[VALKEY_HOST, VALKEY_PORT]],
            "service_name": "pifpaf",
            "db": 0,
            "distributed_lock": True,
        }
    }


class ValkeySentinelAsyncCreationTest(
    _TestValkeySentinelConn, _GenericBackendFixture
):
    backend = "dogpile.cache.valkey_sentinel"
    config_args = {
        "arguments": {
            "sentinels": [[VALKEY_HOST, VALKEY_PORT]],
            "service_name": "pifpaf",
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
