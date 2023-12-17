import os
import sys

from dogpile.cache.backends.file import AbstractFileLock
from dogpile.cache.proxy import ProxyBackend
from dogpile.testing import assert_raises_message
from dogpile.testing.fixtures import _GenericBackendTestSuite
from dogpile.testing.fixtures import _GenericMutexTestSuite
from dogpile.testing.fixtures import _GenericSerializerTestSuite
from dogpile.util.readwrite_lock import ReadWriteMutex

try:
    import fcntl  # noqa

    has_fcntl = True
except ImportError:
    has_fcntl = False


class MutexLock(AbstractFileLock):
    def __init__(self, filename):
        self.mutex = ReadWriteMutex()

    def acquire_read_lock(self, wait):
        ret = self.mutex.acquire_read_lock(wait)
        return wait or ret

    def acquire_write_lock(self, wait):
        ret = self.mutex.acquire_write_lock(wait)
        return wait or ret

    def release_read_lock(self):
        return self.mutex.release_read_lock()

    def release_write_lock(self):
        return self.mutex.release_write_lock()


test_fname = "test_%s.db" % sys.hexversion

if has_fcntl:

    class DBMBackendTest(_GenericBackendTestSuite):
        backend = "dogpile.cache.dbm"

        config_args = {"arguments": {"filename": test_fname}}


class DBMBackendConditionTest(_GenericBackendTestSuite):
    backend = "dogpile.cache.dbm"

    config_args = {
        "arguments": {"filename": test_fname, "lock_factory": MutexLock}
    }


class DBMBackendProxyTest(_GenericBackendTestSuite):
    backend = "dogpile.cache.dbm"

    config_args = {
        "arguments": {"filename": test_fname, "lock_factory": MutexLock},
        "wrap": [ProxyBackend],
    }


class DBMBackendSerializerTest(
    _GenericSerializerTestSuite, DBMBackendConditionTest
):
    pass


class DBMBackendNoLockTest(_GenericBackendTestSuite):
    backend = "dogpile.cache.dbm"

    config_args = {
        "arguments": {
            "filename": test_fname,
            "rw_lockfile": False,
            "dogpile_lockfile": False,
        }
    }


class _DBMMutexTestSuite(_GenericMutexTestSuite):
    backend = "dogpile.cache.dbm"

    def test_release_assertion_thread(self):
        backend = self._backend()
        m1 = backend.get_mutex("foo")
        assert_raises_message(
            AssertionError, "this thread didn't do the acquire", m1.release
        )

    def test_release_assertion_key(self):
        backend = self._backend()
        m1 = backend.get_mutex("foo")
        m2 = backend.get_mutex("bar")

        m1.acquire()
        try:
            assert_raises_message(
                AssertionError, "No acquire held for key 'bar'", m2.release
            )
        finally:
            m1.release()


if has_fcntl:

    class DBMMutexFileTest(_DBMMutexTestSuite):
        config_args = {"arguments": {"filename": test_fname}}


class DBMMutexConditionTest(_DBMMutexTestSuite):
    config_args = {
        "arguments": {"filename": test_fname, "lock_factory": MutexLock}
    }


def teardown():
    for fname in os.listdir(os.curdir):
        if fname.startswith(test_fname):
            os.unlink(fname)
