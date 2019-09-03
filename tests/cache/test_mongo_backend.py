import os
from unittest import TestCase

from mock import Mock
from mock import patch
import pytest

from dogpile.cache.region import _backend_loader
from ._fixtures import _GenericBackendTest
from ._fixtures import _GenericMutexTest

MONGODB_LOCAL_STRING = ""


class _TestMongoConn(object):
    @classmethod
    def _check_backend_available(cls, backend):
        try:
            client = backend._create_client()
            cmd = client.database.command("ping")
            assert cmd == {'ok': 1.0}
        except Exception:
            pytest.skip(
                "mongodb is not running or "
                "otherwise not functioning correctly"
            )


class MongoTest(_TestMongoConn, _GenericBackendTest):
    backend = "dogpile.cache.mongo"
    config_args = {
        "arguments": {
            "mongo_string": "mongodb://localhost:27017",
        }
    }


class MongoDistributedMutexTest(_TestMongoConn, _GenericMutexTest):
    backend = "dogpile.cache.mongo"
    config_args = {
        "arguments": {
            "mongo_string": "mongodb://localhost:27017",
            "distributed_lock": True,
        }
    }
