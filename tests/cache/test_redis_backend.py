from dogpile.cache.region import _backend_loader
from ._fixtures import _GenericBackendTest, _GenericMutexTest
from unittest import TestCase
from mock import patch, Mock
import pytest
import os

REDIS_HOST = '127.0.0.1'
REDIS_PORT = int(os.getenv('DOGPILE_REDIS_PORT', '6379'))
expect_redis_running = os.getenv('DOGPILE_REDIS_PORT') is not None


class _TestRedisConn(object):

    @classmethod
    def _check_backend_available(cls, backend):
        try:
            client = backend._create_client()
            client.set("x", "y")
            # on py3k it appears to return b"y"
            assert client.get("x").decode("ascii") == "y"
            client.delete("x")
        except:
            if not expect_redis_running:
                pytest.skip(
                    "redis is not running or "
                    "otherwise not functioning correctly")
            else:
                raise


class RedisTest(_TestRedisConn, _GenericBackendTest):
    backend = 'dogpile.cache.redis'
    config_args = {
        "arguments": {
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'db': 0,
            "foo": "barf"
        }
    }


class RedisDistributedMutexTest(_TestRedisConn, _GenericMutexTest):
    backend = 'dogpile.cache.redis'
    config_args = {
        "arguments": {
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'db': 0,
            'distributed_lock': True,
        }
    }


@patch('redis.StrictRedis', autospec=True)
class RedisConnectionTest(TestCase):
    backend = 'dogpile.cache.redis'

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
            'host': 'localhost',
            'password': None,
            'port': 6379,
            'db': 0,
        }
        self._test_helper(MockStrictRedis, arguments, {})

    def test_connect_with_basics(self, MockStrictRedis):
        arguments = {
            'host': '127.0.0.1',
            'password': None,
            'port': 6379,
            'db': 0,
        }
        self._test_helper(MockStrictRedis, arguments)

    def test_connect_with_password(self, MockStrictRedis):
        arguments = {
            'host': '127.0.0.1',
            'password': 'some password',
            'port': 6379,
            'db': 0,
        }
        self._test_helper(MockStrictRedis, arguments)

    def test_connect_with_socket_timeout(self, MockStrictRedis):
        arguments = {
            'host': '127.0.0.1',
            'port': 6379,
            'socket_timeout': 0.5,
            'password': None,
            'db': 0,
        }
        self._test_helper(MockStrictRedis, arguments)

    def test_connect_with_connection_pool(self, MockStrictRedis):
        pool = Mock()
        arguments = {
            'connection_pool': pool,
            'socket_timeout': 0.5
        }
        expected_args = {'connection_pool': pool}
        self._test_helper(MockStrictRedis, expected_args,
                          connection_args=arguments)

    def test_connect_with_url(self, MockStrictRedis):
        arguments = {
            'url': 'redis://redis:password@127.0.0.1:6379/0'
        }
        self._test_helper(MockStrictRedis.from_url, arguments)
