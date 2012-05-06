from ._fixtures import _GenericBackendTest, _GenericMutexTest
from . import eq_, assert_raises_message
from unittest import TestCase
from threading import Thread
import time
import os
from nose import SkipTest

try:
    import fcntl
except ImportError:
    raise SkipTest("fcntl not available")

class DBMBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.dbm"

    config_args = {
        "arguments":{
            "filename":"test.dbm"
        }
    }

class DBMBackendNoLockTest(_GenericBackendTest):
    backend = "dogpile.cache.dbm"

    config_args = {
        "arguments":{
            "filename":"test.dbm",
            "rw_lockfile":False,
            "dogpile_lockfile":False,
        }
    }


class DBMMutexTest(_GenericMutexTest):
    backend = "dogpile.cache.dbm"

    config_args = {
        "arguments":{
            "filename":"test.dbm"
        }
    }

    def test_release_assertion_thread(self):
        backend = self._backend()
        m1 = backend.get_mutex("foo")
        assert_raises_message(
            AssertionError,
            "this thread didn't do the acquire",
            m1.release
        )

    def test_release_assertion_key(self):
        backend = self._backend()
        m1 = backend.get_mutex("foo")
        m2 = backend.get_mutex("bar")

        m1.acquire()
        try:
            assert_raises_message(
                AssertionError,
                "No acquire held for key 'bar'",
                m2.release
            )
        finally:
            m1.release()


def teardown():
    for fname in os.listdir(os.curdir):
        if fname.startswith("test.dbm"):
            os.unlink(fname)
