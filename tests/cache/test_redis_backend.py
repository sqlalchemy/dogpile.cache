from ._fixtures import _GenericBackendTest, _GenericMutexTest
from nose import SkipTest

class _TestRedisConn(object):
    @classmethod
    def _check_backend_available(cls, backend):
        try:
            client = backend._create_client()
            client.set("x", "y")
            assert client.get("x") == "y"
            client.delete("x")
        except:
            raise SkipTest(
                "redis is not running or "
                "otherwise not functioning correctly")


class RedisTest(_TestRedisConn, _GenericBackendTest):
    backend = 'dogpile.cache.redis'
    config_args = {
        "arguments":{
            'host': '127.0.0.1',
            'port': 6379,
            'db': 0,
            }
    }


class RedisDistributedMutexTest(_TestRedisConn, _GenericMutexTest):
    backend = 'dogpile.cache.redis'
    config_args = {
        "arguments":{
            'host': '127.0.0.1',
            'port': 6379,
            'db': 0,
            'distributed_lock':True,
            }
    }
