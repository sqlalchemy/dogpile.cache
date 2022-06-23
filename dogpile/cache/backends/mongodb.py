"""
MongoDB Backend
------------------

Provides backends for talking to `MongoDB <https://mongodb.com>`_.

"""

from __future__ import absolute_import

from ..api import CacheBackend
from ..api import NO_VALUE
from ...util.compat import pickle
from datetime import datetime, timedelta
import time

pymongo = None
bson = None

__all__ = ("MongoBackend",)


class MongoMutex(object):
    def __init__(self, collection, key, lock_timeout, client_id, lock_sleep):
        self.collection = collection
        self.key = key
        self.lock_timeout = lock_timeout
        self.client_id = client_id
        self.lock_sleep = lock_sleep

    def acquire(self, blocking=True):
        ac = self._acquire()
        while blocking and not ac:
            ac = self._acquire()
        return ac

    def _acquire(self):
        try:
            doc = self.collection.find_one_and_update(
                {"_id": "LOCKED_{0}".format(self.key),
                 "locked_by": None,
                 "$or": [{"created_at": {"$lte": datetime.utcnow() - timedelta(self.lock_timeout)}},
                         {"created_at": None}]
                 },
                {"$set":
                     {"locked_by": self.client_id,
                      "created_at": datetime.utcnow()}
                 }, upsert=True, return_document=pymongo.collection.ReturnDocument.AFTER)
        except pymongo.errors.DuplicateKeyError:
            doc = False

        if not doc:
            time.sleep(self.lock_sleep)
            return False
        else:
            return True

    def release(self):
        try:
            del_op = self.collection.delete_one(
                {"_id": "LOCKED_{0}".format(self.key), "locked_by": self.client_id}
            )
            if del_op.deleted_count == 1:
                return True
            else:
                return False
        except:
            raise


class MongoBackend(CacheBackend):
    """A `MongoDB <https://mongodb.com/>`_ backend, using the
    `pymongo <https://api.mongodb.com/python/current/>`_ backend.

    Example configuration::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.mongo',
            arguments = {
                'mongo_string': 'mongodb://localhost:27017',
                'database': 'cachingdb',
                'collection': 'cachingcollection',
                'mongo_expiration_time': 60*60*2,   # 2 hours
                'distributed_lock': True
                }
        )

    Arguments accepted in the arguments dictionary:

    :param mongo_string: string. If provided, it will be passed to MongoClient as
     a parameter.  The format is that accepted by ``pymongo.MongoClient()``.

    :param database: string, name of the database.

    :param collection: string, the collection where we will store the data.

    :param mongo_expiration_time: integer, number of seconds after setting
     a value that MongoDB should expire it.  This should be larger than dogpile's
     cache expiration.  By default no expiration is set.

    :param distributed_lock: boolean, when True, will use a
     fancy find_and_modify as the dogpile lock.
     Use this when multiple
     processes will be talking to the same MongoDB instance.
     When left at False, dogpile will coordinate on a regular
     threading mutex.

    :param lock_timeout: integer, number of seconds after acquiring a lock that
     MongoDB should expire it.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param socket_timeout: float, seconds for socket timeout.
     Default is None (no timeout).

    :param lock_sleep: integer, number of seconds to sleep when failed to
     acquire a lock.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    """

    def __init__(self, arguments):
        arguments = arguments.copy()
        self._imports()
        self.mongo_string = arguments.pop("mongo_string", None)
        self.database = arguments.pop("database", "dogpile_locks_database")
        self.collection = arguments.pop("collection", "dogpile_locks_collection")

        self.distributed_lock = arguments.get("distributed_lock", False)
        self.socket_timeout = arguments.pop("socket_timeout", None)

        self.lock_timeout = arguments.get("lock_timeout", 24 * 3600)
        self.lock_sleep = arguments.get("lock_sleep", 0.1)

        self.mongo_expiration_time = arguments.pop("mongo_expiration_time", 0)

        self.client_id = None
        self.client = self._create_client()

    def _imports(self):
        # defer imports until backend is used
        global pymongo, bson
        import pymongo  # noqa
        import bson # noqa

    def _create_client(self):
        args = {'host': self.mongo_string}
        if self.socket_timeout:
            args["connectTimeoutMS"] = self.socket_timeout
        self.client_id = bson.ObjectId()
        collection = pymongo.MongoClient(**args)[self.database][self.collection]
        collection.create_index([("created_at", 1)], expireAfterSeconds=3600 * 24 * 31)
        return collection

    def get_mutex(self, key):
        if self.distributed_lock:
            mtx = MongoMutex(collection=self.client,
                             key=key,
                             lock_timeout=self.lock_timeout,
                             client_id=self.client_id,
                             lock_sleep=self.lock_sleep)
            return mtx
        else:
            return None

    def get(self, key):
        doc = self.client.find_one({"_id": "CACHED_{0}".format(key)})
        if doc is None:
            return NO_VALUE
        return pickle.loads(doc["value"])

    def get_multi(self, keys):
        if not keys:
            return []

        values = self.client.find({"_id": {"$in": ["CACHED_{0}".format(key) for key in keys]}})
        returned = {}

        for doc in values:
            returned[doc["_id"][7:]] = doc["value"]

        to_return = []
        for key in keys:
            if key in returned:
                to_return.append(pickle.loads(returned[key]))
            else:
                to_return.append(NO_VALUE)
        return to_return

    def set(self, key, value):
        if self.mongo_expiration_time:
            self.client.update_one(
                {"_id": "CACHED_{0}".format(key)},
                {"$set": {"value": bson.Binary(pickle.dumps(value, pickle.HIGHEST_PROTOCOL)),
                          "created_at": datetime.utcnow()}
                 }, upsert=True)
        else:
            self.client.update_one(
                {"_id": "CACHED_{0}".format(key)},
                {"$set": {"value": bson.Binary(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))}
                 }, upsert=True)

    def set_multi(self, mapping):

        ops = []
        for k, v in mapping.items():
            if self.mongo_expiration_time:
                set_dict = {"created_at": datetime.utcnow()}
            else:
                set_dict = {}
            set_dict["value"] = bson.Binary(pickle.dumps(v, pickle.HIGHEST_PROTOCOL))
            ops.append(pymongo.UpdateOne({"_id": "CACHED_{0}".format(k)}, {"$set": set_dict}, upsert=True))

        self.client.bulk_write(ops, ordered=False)

    def delete(self, key):
        self.client.delete_one({"_id": "CACHED_{0}".format(key)})

    def delete_multi(self, keys):
        self.client.delete_many({"_id": {"$in": ["CACHED_{0}".format(key) for key in keys]}})
