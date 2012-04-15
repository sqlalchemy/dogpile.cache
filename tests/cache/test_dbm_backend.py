from ._fixtures import _GenericBackendTest, _GenericMutexTest
from . import eq_
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


def teardown():
    for fname in os.listdir(os.curdir):
        if fname.startswith("test.dbm"):
            os.unlink(fname)
