"""
Valkey Backends
------------------

Provides backends for talking to `Valkey <http://valkey.io>`_.

"""

import typing
import warnings

from ..api import BytesBackend
from ..api import NO_VALUE

if typing.TYPE_CHECKING:
    import valkey
else:
    # delayed import
    valkey = None  # noqa F811

__all__ = ("ValkeyBackend", "ValkeySentinelBackend", "ValkeyClusterBackend")


class ValkeyBackend(BytesBackend):
    r"""A `Valkey <http://valkey.io/>`_ backend, using the
    `valkey-py <http://pypi.python.org/pypi/valkey/>`_ driver.

    .. versionadded:: 1.3.4

    Example configuration::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.valkey',
            arguments = {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'valkey_expiration_time': 60*60*2,   # 2 hours
                'distributed_lock': True,
                'thread_local_lock': False
                }
        )


    Arguments accepted in the arguments dictionary:

    :param url: string. If provided, will override separate
     host/username/password/port/db params.  The format is that accepted by
     ``StrictValkey.from_url()``.

    :param host: string, default is ``localhost``.

    :param username: string, default is no username.

    :param password: string, default is no password.

    :param port: integer, default is ``6379``.

    :param db: integer, default is ``0``.

    :param valkey_expiration_time: integer, number of seconds after setting a
     value that Valkey should expire it.  This should be larger than dogpile's
     cache expiration.  By default no expiration is set.

    :param distributed_lock: boolean, when True, will use a
     valkey-lock as the dogpile lock. Use this when multiple processes will be
     talking to the same valkey instance. When left at False, dogpile will
     coordinate on a regular threading mutex.

    :param lock_timeout: integer, number of seconds after acquiring a lock that
     Valkey should expire it.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param socket_timeout: float, seconds for socket timeout.
     Default is None (no timeout).

    :param socket_connect_timeout: float, seconds for socket connection
     timeout. Default is None (no timeout).

    :param socket_keepalive: boolean, when True, socket keepalive is enabled.
     Default is False.

    :param socket_keepalive_options: dict, socket keepalive options.
     Default is None (no options).

    :param lock_sleep: integer, number of seconds to sleep when failed to
     acquire a lock.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param connection_pool: ``valkey.ConnectionPool`` object.  If provided,
     this object supersedes other connection arguments passed to the
     ``valkey.StrictValkey`` instance, including url and/or host as well as
     socket_timeout, and will be passed to ``valkey.StrictValkey`` as the
     source of connectivity.

    :param thread_local_lock: bool, whether a thread-local Valkey lock object
     should be used. This is the default, but is not compatible with
     asynchronous runners, as they run in a different thread than the one
     used to create the lock.

    :param connection_kwargs: dict, additional keyword arguments are passed
     along to the
     ``StrictValkey.from_url()`` method or ``StrictValkey()`` constructor
     directly, including parameters like ``ssl``, ``ssl_certfile``,
     ``charset``, etc.


    """

    def __init__(self, arguments):
        arguments = arguments.copy()
        self._imports()
        self.url = arguments.pop("url", None)
        self.host = arguments.pop("host", "localhost")
        self.username = arguments.pop("username", None)
        self.password = arguments.pop("password", None)
        self.port = arguments.pop("port", 6379)
        self.db = arguments.pop("db", 0)
        self.distributed_lock = arguments.pop("distributed_lock", False)
        self.socket_timeout = arguments.pop("socket_timeout", None)
        self.socket_connect_timeout = arguments.pop(
            "socket_connect_timeout", None
        )
        self.socket_keepalive = arguments.pop("socket_keepalive", False)
        self.socket_keepalive_options = arguments.pop(
            "socket_keepalive_options", None
        )
        self.lock_timeout = arguments.pop("lock_timeout", None)
        self.lock_sleep = arguments.pop("lock_sleep", 0.1)
        self.thread_local_lock = arguments.pop("thread_local_lock", True)
        self.connection_kwargs = arguments.pop("connection_kwargs", {})

        if self.distributed_lock and self.thread_local_lock:
            warnings.warn(
                "The Valkey backend thread_local_lock parameter should be "
                "set to False when distributed_lock is True"
            )

        self.valkey_expiration_time = arguments.pop(
            "valkey_expiration_time", 0
        )
        self.connection_pool = arguments.pop("connection_pool", None)
        self._create_client()

    def _imports(self):
        # defer imports until backend is used
        global valkey
        import valkey  # noqa

    def _create_client(self):
        if self.connection_pool is not None:
            # the connection pool already has all other connection
            # options present within, so here we disregard socket_timeout
            # and others.
            self.writer_client = valkey.StrictValkey(
                connection_pool=self.connection_pool
            )
            self.reader_client = self.writer_client
        else:
            args = {}
            args.update(self.connection_kwargs)
            if self.socket_timeout is not None:
                args["socket_timeout"] = self.socket_timeout
            if self.socket_connect_timeout is not None:
                args["socket_connect_timeout"] = self.socket_connect_timeout
            if self.socket_keepalive:
                args["socket_keepalive"] = True
                if self.socket_keepalive_options is not None:
                    args["socket_keepalive_options"] = (
                        self.socket_keepalive_options
                    )

            if self.url is not None:
                args.update(url=self.url)
                self.writer_client = valkey.StrictValkey.from_url(**args)
                self.reader_client = self.writer_client
            else:
                args.update(
                    host=self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    db=self.db,
                )
                self.writer_client = valkey.StrictValkey(**args)
                self.reader_client = self.writer_client

    def get_mutex(self, key):
        if self.distributed_lock:
            return _ValkeyLockWrapper(
                self.writer_client.lock(
                    "_lock{0}".format(key),
                    timeout=self.lock_timeout,
                    sleep=self.lock_sleep,
                    thread_local=self.thread_local_lock,
                )
            )
        else:
            return None

    def get_serialized(self, key):
        value = self.reader_client.get(key)
        if value is None:
            return NO_VALUE
        return value

    def get_serialized_multi(self, keys):
        if not keys:
            return []
        values = self.reader_client.mget(keys)
        return [v if v is not None else NO_VALUE for v in values]  # type: ignore   # noqa: E501

    def set_serialized(self, key, value):
        if self.valkey_expiration_time:
            self.writer_client.setex(key, self.valkey_expiration_time, value)
        else:
            self.writer_client.set(key, value)

    def set_serialized_multi(self, mapping):
        if not self.valkey_expiration_time:
            self.writer_client.mset(mapping)
        else:
            pipe = self.writer_client.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, self.valkey_expiration_time, value)
            pipe.execute()

    def delete(self, key):
        self.writer_client.delete(key)

    def delete_multi(self, keys):
        self.writer_client.delete(*keys)


class _ValkeyLockWrapper:
    __slots__ = ("mutex", "__weakref__")

    def __init__(self, mutex: typing.Any):
        self.mutex = mutex

    def acquire(self, wait: bool = True) -> typing.Any:
        return self.mutex.acquire(blocking=wait)

    def release(self) -> typing.Any:
        return self.mutex.release()

    def locked(self) -> bool:
        return self.mutex.locked()  # type: ignore


class ValkeySentinelBackend(ValkeyBackend):
    """A `Valkey <http://valkey.io/>`_ backend, using the
    `valkey-py <http://pypi.python.org/pypi/valkey/>`_ driver.
    This backend is to be used when using
    `Valkey Sentinel <https://valkey.io/docs/management/sentinel/>`_.

    .. versionadded:: 1.0.0

    Example configuration::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.valkey_sentinel',
            arguments = {
                'sentinels': [
                    ['valkey_sentinel_1', 26379],
                    ['valkey_sentinel_2', 26379]
                ],
                'db': 0,
                'valkey_expiration_time': 60*60*2,   # 2 hours
                'distributed_lock': True,
                'thread_local_lock': False
            }
        )


    Arguments accepted in the arguments dictionary:

    :param username: string, default is no username.

     .. versionadded:: 1.3.1

    :param password: string, default is no password.

    :param db: integer, default is ``0``.

    :param valkey_expiration_time: integer, number of seconds after setting a
     value that Valkey should expire it.  This should be larger than dogpile's
     cache expiration.  By default no expiration is set.

    :param distributed_lock: boolean, when True, will use a
     valkey-lock as the dogpile lock. Use this when multiple processes will be
     talking to the same valkey instance. When False, dogpile will
     coordinate on a regular threading mutex, Default is True.

    :param lock_timeout: integer, number of seconds after acquiring a lock that
     Valkey should expire it.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param socket_timeout: float, seconds for socket timeout.
     Default is None (no timeout).

     .. versionadded:: 1.3.2

    :param socket_connect_timeout: float, seconds for socket connection
     timeout.  Default is None (no timeout).

     .. versionadded:: 1.3.2

    :param socket_keepalive: boolean, when True, socket keepalive is enabled
     Default is False.

     .. versionadded:: 1.3.2

    :param socket_keepalive_options: dict, socket keepalive options.
     Default is {} (no options).

    :param sentinels: is a list of sentinel nodes. Each node is represented by
     a pair (hostname, port).
     Default is None (not in sentinel mode).

    :param service_name: str, the service name.
     Default is 'mymaster'.

    :param sentinel_kwargs: is a dictionary of connection arguments used when
     connecting to sentinel instances. Any argument that can be passed to
     a normal Valkey connection can be specified here.
     Default is {}.

    :param connection_kwargs: dict, additional keyword arguments are passed
     along to the
     ``StrictValkey.from_url()`` method or ``StrictValkey()`` constructor
     directly, including parameters like ``ssl``, ``ssl_certfile``,
     ``charset``, etc.

    :param lock_sleep: integer, number of seconds to sleep when failed to
     acquire a lock.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param thread_local_lock: bool, whether a thread-local Valkey lock object
     should be used. This is the default, but is not compatible with
     asynchronous runners, as they run in a different thread than the one
     used to create the lock.


    """

    def __init__(self, arguments):
        arguments = arguments.copy()

        self.sentinels = arguments.pop("sentinels", None)
        self.service_name = arguments.pop("service_name", "mymaster")
        self.sentinel_kwargs = arguments.pop("sentinel_kwargs", {})

        super().__init__(
            arguments={
                "distributed_lock": True,
                "thread_local_lock": False,
                **arguments,
            }
        )

    def _imports(self):
        # defer imports until backend is used
        global valkey
        import valkey.sentinel  # noqa

    def _create_client(self):
        sentinel_kwargs = {}
        sentinel_kwargs.update(self.sentinel_kwargs)
        sentinel_kwargs.setdefault("username", self.username)
        sentinel_kwargs.setdefault("password", self.password)

        connection_kwargs = {}
        connection_kwargs.update(self.connection_kwargs)
        connection_kwargs.setdefault("username", self.username)
        connection_kwargs.setdefault("password", self.password)

        if self.db is not None:
            connection_kwargs.setdefault("db", self.db)
            sentinel_kwargs.setdefault("db", self.db)
        if self.socket_timeout is not None:
            connection_kwargs.setdefault("socket_timeout", self.socket_timeout)
        if self.socket_connect_timeout is not None:
            connection_kwargs.setdefault(
                "socket_connect_timeout", self.socket_connect_timeout
            )
        if self.socket_keepalive:
            connection_kwargs.setdefault("socket_keepalive", True)
            if self.socket_keepalive_options is not None:
                connection_kwargs.setdefault(
                    "socket_keepalive_options", self.socket_keepalive_options
                )

        sentinel = valkey.sentinel.Sentinel(
            self.sentinels,
            sentinel_kwargs=sentinel_kwargs,
            **connection_kwargs,
        )
        self.writer_client = sentinel.master_for(self.service_name)
        self.reader_client = sentinel.slave_for(self.service_name)


class ValkeyClusterBackend(ValkeyBackend):
    r"""A `Valkey <http://valkey.io/>`_ backend, using the
    `valkey-py <http://pypi.python.org/pypi/valkey/>`_ driver.
    This backend is to be used when connecting to a
    `Valkey Cluster <https://valkey.io/docs/management/scaling/>`_ which
    will use the
    `ValkeyCluster Client
    <https://valkey.readthedocs.io/en/stable/connections.html#cluster-client>`_.

    .. seealso::

        `Clustering <https://valkey.readthedocs.io/en/stable/clustering.html>`_
        in the valkey-py documentation.

    Requires valkey-py version >=4.1.0.

    .. versionadded:: 1.3.2

    Connecting to the cluster requires one of:

    * Passing a list of startup nodes
    * Passing only one node of the cluster, Valkey will use automatic discovery
      to find the other nodes.

    Example configuration, using startup nodes::

        from dogpile.cache import make_region
        from valkey.cluster import ClusterNode

        region = make_region().configure(
            'dogpile.cache.valkey_cluster',
            arguments = {
                "startup_nodes": [
                    ClusterNode('localhost', 6379),
                    ClusterNode('localhost', 6378)
                ]
            }
        )

    It is recommended to use startup nodes, so that connections will be
    successful as at least one node will always be present.  Connection
    arguments such as password, username or
    CA certificate may be passed using ``connection_kwargs``::

        from dogpile.cache import make_region
        from valkey.cluster import ClusterNode

        connection_kwargs = {
            "username": "admin",
            "password": "averystrongpassword",
            "ssl": True,
            "ssl_ca_certs": "valkey.pem",
        }

        nodes = [
            ClusterNode("localhost", 6379),
            ClusterNode("localhost", 6380),
            ClusterNode("localhost", 6381),
        ]

        region = make_region().configure(
            "dogpile.cache.valkey_cluster",
            arguments={
                "startup_nodes": nodes,
                "connection_kwargs": connection_kwargs,
            },
        )

    Passing a URL to one node only will allow the driver to discover the whole
    cluster automatically::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.valkey_cluster',
            arguments = {
                "url": "localhost:6379/0"
            }
        )

    A caveat of the above approach is that if the single node targeting
    is not available, this would prevent the connection from being successful.

    Parameters accepted include:

    :param startup_nodes: List of ClusterNode. The list of nodes in
     the cluster that the client will try to connect to.

    :param url: string. If provided, will override separate
     host/password/port/db params.  The format is that accepted by
     ``ValkeyCluster.from_url()``.

    :param db: integer, default is ``0``.

    :param valkey_expiration_time: integer, number of seconds after setting
     a value that Valkey should expire it.  This should be larger than dogpile's
     cache expiration.  By default no expiration is set.

    :param distributed_lock: boolean, when True, will use a
     valkey-lock as the dogpile lock. Use this when multiple processes will be
     talking to the same valkey instance. When left at False, dogpile will
     coordinate on a regular threading mutex.

    :param lock_timeout: integer, number of seconds after acquiring a lock that
     Valkey should expire it.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param socket_timeout: float, seconds for socket timeout.
     Default is None (no timeout).

    :param socket_connect_timeout: float, seconds for socket connection
     timeout.  Default is None (no timeout).

    :param socket_keepalive: boolean, when True, socket keepalive is enabled
     Default is False.

    :param lock_sleep: integer, number of seconds to sleep when failed to
     acquire a lock.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param thread_local_lock: bool, whether a thread-local Valkey lock object
     should be used. This is the default, but is not compatible with
     asynchronous runners, as they run in a different thread than the one
     used to create the lock.

    :param connection_kwargs: dict, additional keyword arguments are passed
     along to the
     ``ValkeyCluster.from_url()`` method or ``ValkeyCluster()`` constructor
     directly, including parameters like ``ssl``, ``ssl_certfile``,
     ``charset``, etc.

    """  # noqa: E501

    def __init__(self, arguments):
        arguments = arguments.copy()
        self.startup_nodes = arguments.pop("startup_nodes", None)
        super().__init__(arguments)

    def _imports(self):
        global valkey
        import valkey.cluster

    def _create_client(self):
        valkey_cluster: valkey.cluster.ValkeyCluster[typing.Any]  # type: ignore   # noqa: E501
        if self.url is not None:
            valkey_cluster = valkey.cluster.ValkeyCluster.from_url(
                self.url, **self.connection_kwargs
            )
        else:
            valkey_cluster = valkey.cluster.ValkeyCluster(  # type: ignore   # noqa: E501
                startup_nodes=self.startup_nodes,
                **self.connection_kwargs,
            )
        self.writer_client = typing.cast(valkey.Valkey[bytes], valkey_cluster)  # type: ignore   # noqa: E501
        self.reader_client = self.writer_client
