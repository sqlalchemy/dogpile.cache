"""
Redis Backends
------------------

Provides backends for talking to `redis <http://redis.io>`_.

"""

from __future__ import absolute_import
from dogpile.cache.api import CacheBackend, NO_VALUE
from dogpile.cache.util import pickle
import random
import time

class RedisBackend(CacheBackend):
    """A `Redis <http://redis.io/>`_ backend.

    Example configuration::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.redis',
            arguments = {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'redis_expiration_time': 60*60*2,   # 2 hours
                }
        )

    Arguments accepted in the arguments dictionary:

    :param host: string, default is ``localhost``.

    :param port: integer, default is ``6379``.

    :param db: integer, default is ``0``.

    :param redis_expiration_time: integer, number of seconds after setting
    a value that Redis should expire it.  This should be larger than dogpile's
    cache expiration.  By default no expiration is set.
    """

    def __init__(self, arguments):
        self._imports()
        self.host = arguments.pop('host', 'localhost')
        self.port = arguments.pop('port', 6379)
        self.db = arguments.pop('db', 0)
        self.distributed_lock = arguments.get('distributed_lock', False)
        self.redis_expiration_time = arguments.pop('redis_expiration_time', 0)
        self.client = self._create_client()

    def _imports(self):
        # defer imports until backend is used
        global redis
        import redis

    def _create_client(self):
        # creates client instace (so test harness can test connection)
        return redis.StrictRedis(host=self.host, port=self.port, db=self.db)

    def get_mutex(self, key):
        if self.distributed_lock:
            return RedisLock(lambda: self.client, key)
        else:
            return None

    def get(self, key):
        value = self.client.get(key)
        if value is None:
            return NO_VALUE
        return pickle.loads(value)

    def set(self, key, value):
        if self.redis_expiration_time:
            self.client.setex(key, self.redis_expiration_time,
                    pickle.dumps(value))
        else:
            self.client.set(key, pickle.dumps(value))

    def delete(self, key):
        self.client.delete(key)

class RedisLock(object):
    def __init__(self, client_fn, key):
        self.client_fn = client_fn
        self.key = "_lock" + key

    def acquire(self, wait=True):
        client = self.client_fn()
        i = 0
        while True:
            if client.setnx(self.key, 1):
                return True
            elif not wait:
                return False
            else:
                sleep_time = (((i+1)*random.random()) + 2**i) / 2.5
                time.sleep(sleep_time)
            if i < 15:
                i += 1

    def release(self):
        client = self.client_fn()
        client.delete(self.key)


