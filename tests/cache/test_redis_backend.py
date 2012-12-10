from dogpile.cache.region import _backend_loader
from ._fixtures import _GenericBackendTest, _GenericMutexTest
from unittest import TestCase
from nose import SkipTest
from mock import patch

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
            raise SkipTest(
                "redis is not running or "
                "otherwise not functioning correctly")


class RedisTest(_TestRedisConn, _GenericBackendTest):
    backend = 'dogpile.cache.redis'
    config_args = {
        "arguments": {
            'host': '127.0.0.1',
            'port': 6379,
            'db': 0,
            }
    }


class RedisDistributedMutexTest(_TestRedisConn, _GenericMutexTest):
    backend = 'dogpile.cache.redis'
    config_args = {
        "arguments": {
            'host': '127.0.0.1',
            'port': 6379,
            'db': 0,
            'distributed_lock': True,
            }
    }

@patch('redis.StrictRedis', autospec=True)
class RedisConnectionTest(TestCase):
    backend = 'dogpile.cache.redis'

    @classmethod
    def setup_class(cls):
        try:
            cls.backend_cls = _backend_loader.load(cls.backend)
            cls.backend_cls({})
        except ImportError:
            raise SkipTest("Backend %s not installed" % cls.backend)

    def _test_helper(self, mock_obj, expected_args, connection_args=None):
        if connection_args is None:
            # The redis backend pops items from the dict, so we copy
            connection_args = expected_args.copy()

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

    def test_connect_with_url(self, MockStrictRedis):
        arguments = {
            'url': 'redis://redis:password@127.0.0.1:6379/0'
        }
        self._test_helper(MockStrictRedis.from_url, arguments)