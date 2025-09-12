=========
Changelog
=========

.. changelog::
    :version: 1.4.1
    :released: Fri Sep 12 2025

    .. change::
        :tags: usecase, redis
        :tickets: 271

        Added new parameters :paramref:`.RedisBackend.lock_blocking_timeout` and
        :paramref:`.RedisBackend.lock_blocking` to the Redis backend; and
        :paramref:`.ValkeyBackend.lock_blocking_timeout` and
        :paramref:`.ValkeyBackend.lock_blocking` to the Valkey backends.  These
        parameters are then passed onto the redis/valkey client Lock creation
        methods and use the same defaults.

    .. change::
        :tags: bug, memory
        :tickets: 273

        Fixed issue where :meth:`.MemoryBackend.configure` would unexpectedly
        modify the input arguments dictionary by removing its contents. The method
        now preserves the original arguments dictionary as expected, consistent
        with the behavior of other backend types.  Pull request courtesy Nicolas
        Simonds.

    .. change::
        :tags: usecase, redis
        :tickets: 276

        Added new parameters for the Redis/Valkey backends. These params are passed
        directly to the constructors:

        * :paramref:`.RedisBackend.ssl`
        * :paramref:`.ValkeyBackend.ssl`

        These params default to ``None``, and are only passed to the constructor if
        set. The docstrings instruct users to submit all additional ``ssl_``
        prefixed params via the optional
        :paramref:`.RedisBackend.connection_kwargs` or
        :paramref:`.ValkeyBackend.connection_kwargs` parameter.

.. changelog::
    :version: 1.4.0
    :released: Sat Apr 26 2025

    .. change::
        :tags: change, general

        Support for Python 3.8 has been dropped, the minimum version is now Python
        3.9, as 3.8 is EOL.   This change is necessitated by the need to require
        setuptools 77.0.3 in order to satisfy :pep:`639`.



    .. change::
        :tags: bug, general

        The pyproject.toml configuration has been amended to use
        the updated :pep:`639` configuration for license, which eliminates
        loud deprecation warnings when building the package.   Note this
        necessarily bumps setuptools build requirement to 77.0.3 which
        forces Python 3.8 support to be dropped.


.. changelog::
    :version: 1.3.4
    :released: Tue Jan 28 2025

    .. change::
        :tags: bug, redis
        :tickets: 263

        Fixes to the recently added ``RedisClusterBackend`` fixing a runtime typing
        error that prevented it from running.

    .. change::
        :tags: change, general

        The pin for ``setuptools<69.3`` in ``pyproject.toml`` has been removed.
        This pin was to prevent a sudden change to :pep:`625` in setuptools from
        taking place which changes the file name of SQLAlchemy's source
        distribution on pypi to be an all lower case name, and the change was
        extended to all SQLAlchemy projects to prevent any further surprises.
        However, the presence of this pin is now holding back environments that
        otherwise want to use a newer setuptools, so we've decided to move forward
        with this change, with the assumption that build environments will have
        largely accommodated the setuptools change by now.





    .. change::
        :tags: usecase, valkey

        Added backend for valkey server.  This is based on valkey-py as the driver.

        .. seealso::

            :class:`.ValkeyBackend`



.. changelog::
    :version: 1.3.3
    :released: Sun May 5 2024

    .. change::
        :tags: bug, typing

        Fixed the return type for :meth:`.CacheRegion.get`, which was inadvertently
        hardcoded to use ``CacheReturnType`` that only resolved to ``CachedValue``
        or ``NoValue``.   Fixed to return ``ValuePayload`` which resolves to
        ``Any``, as well as a new literal indicating an enum constant for
        :data:`.api.NO_VALUE`.  The :data:`.api.NO_VALUE` constant remains
        available as the single element of this enum.

    .. change::
        :tags: usecase, memcached

        Added support for an additional pymemcached client parameter
        :paramref:`.PyMemcacheBackend.memcached_expire_time`.  Pull request
        courtesy Takashi Kajinami.

.. changelog::
    :version: 1.3.2
    :released: Wed Feb 21 2024

    .. change::
        :tags: usecase, redis
        :tickets: 250

        Added a new backend :class:`.RedisClusterBackend`, allowing support for
        Redis Cluster.  Pull request courtesy Maël Naccache Tüfekçi.


    .. change::
        :tags: usecase, redis
        :tickets: 252

        Added support for additional Redis client parameters
        :paramref:`.RedisBackend.socket_connect_timeout`,
        :paramref:`.RedisBackend.socket_keepalive` and
        :paramref:`.RedisBackend.socket_keepalive_options`. Pull request courtesy
        Takashi Kajinami.

.. changelog::
    :version: 1.3.1
    :released: Wed Feb 7 2024

    .. change::
        :tags: usecase, redis

        Added new parameter :paramref:`.RedisBackend.username` to the Redis
        backend, and :paramref:`.RedisSentinelBackend.username` to the Redis
        Sentinel backend.  These parameters allow for username authentication in
        Redis when RBAC is enabled.   Pull request courtesy Takashi Kajinami.

.. changelog::
    :version: 1.3.0
    :released: Wed Dec 20 2023

    .. change::
        :tags: feature, region
        :tickets: 37

        Added new method :meth:`.CacheRegion.get_value_metadata` which can be used
        to get a value from the cache along with its metadata, including timestamp
        of when the value was cached.  The :class:`.CachedValue` object is returned
        which features new accessors to retrieve cached time and current age. Pull
        request courtesy Grégoire Deveaux.



    .. change::
        :tags: change, setup

        Minimum Python version is now Python 3.8; prior versions Python 3.7 and 3.6
        are EOL.


    .. change::
        :tags: change, setup

        Project setup is now based on pep-621 ``pyproject.toml`` configuration.

.. changelog::
    :version: 1.2.2
    :released: Sat Jul 8 2023

    .. change::
        :tags: bug, typing
        :tickets: 240

        Made use of pep-673 ``Self`` type for method chained methods such as
        :meth:`.CacheRegion.configure` and :meth:`.ProxyBackend.wrap`. Pull request
        courtesy Viicos.

.. changelog::
    :version: 1.2.1
    :released: Sat May 20 2023

    .. change::
        :tags: bug, typing
        :tickets: 238

        Added py.typed file to root so that typing tools such as Mypy recognize
        dogpile as typed. Pull request courtesy Daverball.

.. changelog::
    :version: 1.2.0
    :released: Wed Apr 26 2023

    .. change::
        :tags: feature, region
        :tickets: 236

        Added new construct :class:`.api.CantDeserializeException` which can be
        raised by user-defined deserializer functions which would be passed to
        :paramref:`.CacheRegion.deserializer`, to indicate a cache value that can't
        be deserialized and therefore should be regenerated. This can allow an
        application that's been updated to gracefully re-cache old items that were
        persisted from a previous version of the application. Pull request courtesy
        Simon Hewitt.

.. changelog::
    :version: 1.1.8
    :released: Fri Jul 8 2022

    .. change::
        :tags: bug, memcached
        :tickets: 223, 228

        Moved the :paramref:`.MemcacheArgs.dead_retry` argument and the
        :paramref:`.MemcacheArgs.socket_timeout` argument which were
        erroneously added to the "set_parameters",
        where they have no effect, to be part of the Memcached connection
        arguments :paramref:`.MemcachedBackend.dead_retry`,
        :paramref:`.MemcachedBackend.socket_timeout`.


.. changelog::
    :version: 1.1.7
    :released: Tue Jul 5 2022

    .. change::
           :tags: usecase, memcached
           :tickets: 223

           Added :paramref:`.MemcacheArgs.dead_retry` and
           :paramref:`.MemcacheArgs.socket_timeout` to the dictionary of
           additional keyword arguments that will be passed
           directly to ``GenericMemcachedBackend()``.

.. changelog::
    :version: 1.1.6
    :released: Fri Jun 10 2022

    .. change::
        :tags: bug, redis
        :tickets: 220

        Fixed regression caused by backwards-incompatible API changes in Redis that
        caused the "distributed lock" feature to not function.

    .. change::
        :tags: usecase, redis
        :tickets: 221

        Added :paramref:`.RedisBackend.connection_kwargs` parameter, which is a
        dictionary of additional keyword arguments that will be passed directly to
        ``StrictRedis()`` or ``StrictRedis.from_url()``, in the same way that this
        parameter works with the :class:`.RedisSentinelBackend` already.

.. changelog::
    :version: 1.1.5
    :released: Wed Jan 19 2022

    .. change::
        :tags: usecase, memcached

        Added support for additional pymemcache ``HashClient`` parameters
        ``retry_attempts``, ``retry_timeout``, and
        ``dead_timeout``.

        .. seealso::

            :paramref:`.PyMemcacheBackend.hashclient_retry_attempts`

            :paramref:`.PyMemcacheBackend.hashclient_retry_timeout`

            :paramref:`.PyMemcacheBackend.dead_timeout`

.. changelog::
    :version: 1.1.4
    :released: Thu Sep 2 2021

    .. change::
        :tags: bug, general
        :tickets: 203

        Fixed Python 3.10 deprecation warning involving threading. Pull request
        courtesy Karthikeyan Singaravelan.

    .. change::
        :tags: usecase, memcached

        Added support for pymemcache socket keepalive and retrying client.

        .. seealso::

            :paramref:`.PyMemcacheBackend.socket_keepalive`

            :paramref:`.PyMemcacheBackend.enable_retry_client`

.. changelog::
    :version: 1.1.3
    :released: Thu May 20 2021

    .. change::
        :tags: bug, regression, tests

        Repaired the test suite to work with the 5.x series of the ``decorator``
        module, which now appears to make use of the ``__signature__`` attribute.

    .. change::
        :tags: bug, regression
        :tickets: 202

        Fixed regression where :class:`.ProxyBackend` was missing several methods
        that were added as part of the 1.1 release.

.. changelog::
    :version: 1.1.2
    :released: Tue Jan 26 2021

    .. change::
        :tags: feature, region
        :tickets: 101

        Added new region method :meth:`.CacheRegion.key_is_locked`. Returns True if
        the given key is subject to the dogpile lock, which would indicate that the
        generator function is running at that time. Pull request courtesy Bastien
        Gerard.

    .. change::
        :tags: feature, memcached
        :tickets: 134

        Added support for the pymemcache backend, using the
        ``"dogpile.cache.pymemcache"`` backend identifier. Pull request courtesy
        Moisés Guimarães de Medeiros.

        .. seealso::

          :class:`.PyMemcacheBackend`

.. changelog::
    :version: 1.1.1
    :released: Mon Nov 23 2020

    .. change::
        :tags: bug, region
        :tickets: 195

        Fixed regression where the serialization and deserialization functions
        could be inadvertently turned into instance methods with an unexpected
        argument signature, namely when pickle.dumps and pickle.loads are the pure
        Python version as is the case in pypy.


.. changelog::
    :version: 1.1.0
    :released: Sun Nov 15 2020

    .. change::
        :tags: feature, region
        :tickets: 191

        Reworked the means by which values are serialized and deserialized from
        backends, and provided for custom serialization of values.  Added the
        :paramref:`.CacheRegion.serializer` and
        :paramref:`.CacheRegion.deserializer` parameters which may be set to any
        serializer.

        Serialization and deserialization now take place within the
        :class:`.CacheRegion` so that backends may now assume string values
        in all cases.  This simplifies the existing backends and also makes
        custom backends easier to write and maintain.

        Additionally, the serializer is now applied to the user-defined value
        portion of the :class:`.CachedValue` and not to the metadata or other
        portions of :class:`.CachedValue` object itself, so the serialized portion
        is effectively a "payload" within the larger :class:`.CachedValue`
        structure that is passed as part of the larger string format.  The overall
        format is a separate JSON of the cached value metadata, followed by the
        serialized form.  This allows for end-user serialization schemes that are
        hardwired to the values themselves without the need to serialize dogpile's
        internal structures as well.

        Existing custom backends should continue to work without issue;  they
        now have the option to forego any separate serialization steps, and
        can also subclass a new backend :class:`.BytesBackend` that marks them
        as a backend that only deals with bytes coming in and out; all
        internal serialization logic from such a backend can be removed.

        Pull request courtesy Alessio Bogon.

    .. change::
        :tags: change

        Added pep-484 annotations to most of the dogpile.cache package.

.. changelog::
    :version: 1.0.2
    :released: Fri Aug 7 2020

    .. change::
        :tags: feature, memcached
        :tickets: 173

        Added support for TLS connections to the bmemcached backend.  Pull request
        courtesy Moisés Guimarães de Medeiros.

    .. change::
        :tags: bug, installation

        Repaired the setup.cfg file so that the source and wheel distributions will
        not add the "tests" directory to the Python environment.   Pull request
        courtesy Michał Górny.


.. changelog::
    :version: 1.0.1
    :released: Tue Jul 21 2020

    .. change::
        :tags: bug, install
        :tickets: 184

        dogpile.cache 1.0.0 was released with a minimum Python version of 3.5.
        However, due to a dependency issue, the minimum version is now Python 3.6.
        The 1.0.0 release will be removed from PyPI so that Python versions prior
        to 3.6 will continue to make use of the previous dogpile.cache 0.9.2.

    .. change::
        :tags: bug, installation
        :tickets: 185

        Removed the "universal=1" directive from setup.cfg as this would create
        py2/py3 wheels.   dogpile 1.0.x is Python 3 only so a py3-only wheel is now
        created.

.. changelog::
    :version: 1.0.0
    :released: Sun Jul 19 2020

    .. change::
        :tags: change: py3k

        For version 1.0.0, dogpile.cache now supports Python 3.5 and above
        only.


    .. change::
       :tags: feature

       Improved plugin scanner performance by switching from pkg_resources
       to stevedore.

    .. change::
        :tags: feature, redis
        :tickets: 181

        Added support for Redis Sentinel.  Pull request courtesy Stéphane Brunner.
        See :class:`.RedisSentinelBackend`.

.. changelog::
    :version: 0.9.2
    :released: Mon May 4 2020

    .. change::
        :tags: bug, installation
        :tickets: 178

        Ensured that the "pyproject.toml" file is not included in builds, as the
        presence of this file indicates to pip that a pep-517 installation process
        should be used.  As this mode of operation appears to be not well supported
        by current tools / distros, these problems are avoided within the scope of
        dogpile.cache installation by omitting the file.


.. changelog::
    :version: 0.9.1
    :released: Wed Apr 29 2020

    .. change::
        :tags: bug, tests

        Added ``decorator`` module as a required testing dependency to
        ``tox.ini`` so that tests work when this is not pre-installed.

    .. change::
        :tags: bug, redis
        :tickets: 171

        Added option to the Redis backend
        :paramref:`.RedisBackend.thread_local_lock`, which when set to False will
        disable the use of a threading local  by the ``redis`` module in its
        distributed lock service, which is known to interfere with the lock's
        behavior when used in an "async" use case, within dogpile this would be
        when using the :paramref:`.CacheRegion.async_creation_runner` feature. The
        default is conservatively being left at True, but it's likely this should
        be set to False in all cases, so a warning is emitted if this flag is not
        set to False in conjunction with the distributed lock. Added an optional
        argument to :class:`.RedisBackend` that specifies whether or not a
        thread-local Redis lock should be used.  This is the default, but it breaks
        asynchronous runner compatibility.

.. changelog::
    :version: 0.9.0
    :released: Mon Oct 28 2019

    .. change::
        :tags: feature

        Added logging facililities into :class:`.CacheRegion`, to indicate key
        events such as cache keys missing or regeneration of values.  As these can
        be very high volume log messages, ``logging.DEBUG`` is used as the log
        level for the events.  Pull request courtesy Stéphane Brunner.



.. changelog::
    :version: 0.8.0
    :released: Fri Sep 20 2019

    .. change::
        :tags: bug, setup
        :tickets: 157

        Removed the "python setup.py test" feature in favor of a straight run of
        "tox".   Per Pypa / pytest developers, "setup.py" commands are in general
        headed towards deprecation in favor of tox.  The tox.ini script has been
        updated such that running "tox" with no arguments will perform a single run
        of the test suite against the default installed Python interpreter.

        .. seealso::

            https://github.com/pypa/setuptools/issues/1684

            https://github.com/pytest-dev/pytest/issues/5534


    .. change::
        :tags: bug, py3k
        :tickets: 154

        Replaced the Python compatbility routines for ``getfullargspec()`` with a
        fully vendored version from Python 3.3.  Originally, Python was emitting
        deprecation warnings for this function in Python 3.8 alphas.  While this
        change was reverted, it was observed that Python 3 implementations for
        ``getfullargspec()`` are an order of magnitude slower as of the 3.4 series
        where it was rewritten against ``Signature``.  While Python plans to
        improve upon this situation, SQLAlchemy projects for now are using a simple
        replacement to avoid any future issues.



    .. change::
        :tags: bug, installation
        :tickets: 160

        Pinned minimum version of Python decorator module at 4.0.0 (July, 2015) as
        previous versions don't provide the API that dogpile is using.

    .. change::
        :tags: bug, py3k
        :tickets: 159

        Fixed the :func:`.sha1_mangle_key` key mangler to coerce incoming Unicode
        objects into bytes as is required by the Py3k version of this function.


.. changelog::
    :version: 0.7.1
    :released: Tue Dec 11 2018

    .. change::
       :tags: bug, region
       :tickets: 139

       Fixed regression in 0.7.0 caused by :ticket:`136` where the assumed
       arguments for the :paramref:`.CacheRegion.async_creation_runner` expanded to
       include the new :paramref:`.CacheRegion.get_or_create.creator_args`
       parameter, as it was not tested that the async runner would be implicitly
       called with these arguments when the :meth:`.CacheRegion.cache_on_arguments`
       decorator was used.  The exact signature of ``async_creation_runner`` is
       now restored to have the same arguments in all cases.


.. changelog::
    :version: 0.7.0
    :released: Mon Dec 10 2018

    .. change::
        :tags: bug
        :tickets: 137

        The ``decorator`` module is now used when creating function decorators
        within :meth:`.CacheRegion.cache_on_arguments` and
        :meth:`.CacheRegion.cache_multi_on_arguments` so that function signatures
        are preserved.  Pull request courtesy ankitpatel96.

        Additionally adds a small performance enhancement which is to avoid
        internally creating a ``@wraps()`` decorator for the creator function on
        every get operation, by allowing the arguments to the creator be passed
        separately to :meth:`.CacheRegion.get_or_create`.


    .. change::
       :tags: bug, py3k
       :tickets: 129

       Fixed all Python 3.x deprecation warnings including
       ``inspect.getargspec()``.

.. changelog::
    :version: 0.6.8
    :released: Sat Nov 24 2018

    .. change::
       :tags: change

       Project hosting has moved to GitHub, under the SQLAlchemy
       organization at https://github.com/sqlalchemy/dogpile.cache

.. changelog::
    :version: 0.6.7
    :released: Thu Jul 26 2018

    .. change::
        :tags: bug
        :tickets: 128

        Fixed issue in the :meth:`.CacheRegion.get_or_create_multi` method which
        was erroneously considering the cached value as the timestamp field if the
        :meth:`.CacheRegion.invalidate` method had ben used, usually causing a
        ``TypeError`` to occur, or in less frequent cases an invalid result for
        whether or not the cached value was invalid, leading to excessive caching
        or regeneration. The issue was a regression caused by an implementation
        issue in the pluggable invalidation feature added in :ticket:`38`.

.. changelog::
    :version: 0.6.6
    :released: Wed Jun 27 2018

    .. change::
        :tags: feature
        :tickets: 123

        Added method :attr:`.CacheRegion.actual_backend` which calculates and
        caches the actual backend for the region, which may be abstracted by
        the use of one or more :class:`.ProxyBackend` subclasses.




    .. change::
        :tags: bug
        :tickets: 122

        Fixed a condition in the :class:`.Lock` where the "get" function could be
        called a second time unnecessarily, when returning an existing, expired
        value from the cache.

.. changelog::
    :version: 0.6.5
    :released: Mon Mar 5 2018

    .. change::
    	:tags: bug
    	:tickets: 119

    	Fixed import issue for Python 3.7 where several variables named "async"
    	were, leading to syntax errors.  Pull request courtesy Brian Sheldon.



.. changelog::
    :version: 0.6.4
    :released: Mon Jun 26, 2017

    .. change::
      :tags: bug

      The method :meth:`.Region.get_or_create_multi` will not pass to the
      cache backend if no values are ultimately to be stored, based on
      the use of the :paramref:`.Region.get_or_create_multi.should_cache_fn`
      function.  This empty dictionary is unnecessary and can cause API
      problems for backends like that of Redis.  Pull request courtesy
      Tobias Sauerwein.

    .. change::
      :tags: bug

      The :attr:`.api.NO_VALUE` constant now has a fixed ``__repr__()``
      output, so that scenarios where this constant's string value
      ends up being used as a cache key do not create multiple values.
      Pull request courtesy Paul Brown.

    .. change::
      :tags: bug

      A new exception class :class:`.exception.PluginNotFound` is now
      raised when a particular cache plugin class cannot be located
      either as a setuptools entrypoint or as a registered backend.
      Previously, a plain ``Exception`` was thrown.  Pull request
      courtesy Jamie Lennox.

.. changelog::
    :version: 0.6.3
    :released: Thu May 18, 2017

    .. change::
      :tags: feature

      Added ``replace_existing_backend`` to
      :meth:`.CacheRegion.configure_from_config`.
      Pull request courtesy Daniel Kraus.

.. changelog::
    :version: 0.6.2
    :released: Tue Aug 16 2016

    .. change::
      :tags: feature
      :tickets: 38

      Added a new system to allow custom plugins specific to the issue of
      "invalidate the entire region", using a new base class
      :class:`.RegionInvalidationStrategy`. As there are many potential
      strategies to this (special backend function, storing special keys, etc.)
      the mechanism for both soft and hard invalidation is now customizable.
      New approaches to region invalidation can be contributed as documented
      recipes.  Pull request courtesy Alexander Makarov.

    .. change::
      :tags: feature
      :tickets: 43

      Added a new cache key generator :func:`.kwarg_function_key_generator`,
      which takes keyword arguments as well as positional arguments into
      account when forming the cache key.

    .. change::
      :tags: bug

      Restored some more util symbols that users may have been relying upon
      (although these were not necessarily intended as user-facing):
      ``dogpile.cache.util.coerce_string_conf``,
      ``dogpile.cache.util.KeyReentrantMutex``,
      ``dogpile.cache.util.memoized_property``,
      ``dogpile.cache.util.PluginLoader``,
      ``dogpile.cache.util.to_list``.

.. changelog::
    :version: 0.6.1
    :released: Mon Jun 6 2016

    .. change::
      :tags: bug
      :tickets: 99

      Fixed imports for ``dogpile.core`` restoring ``ReadWriteMutex``
      and ``NameRegistry`` into the base namespace, in addition to
      ``dogpile.core.nameregistry`` and ``dogpile.core.readwrite_lock``.

.. changelog::
    :version: 0.6.0
    :released: Mon Jun 6 2016

    .. change::
      :tags: feature
      :tickets: 91

      The ``dogpile.core`` library has been rolled in as part of the
      ``dogpile.cache`` distribution.   The configuration of the ``dogpile``
      name as a namespace package is also removed from ``dogpile.cache``.
      In order to allow existing installations of ``dogpile.core`` as a separate
      package to remain unaffected, the ``.core`` package has been retired
      within ``dogpile.cache`` directly; the :class:`.Lock` class is now
      available directly as ``dogpile.Lock`` and the additional ``dogpile.core``
      constructs are under the ``dogpile.util`` namespace.

      Additionally, the long-deprecated ``dogpile.core.Dogpile`` and
      ``dogpile.core.SyncReaderDogpile`` classes have been removed.

    .. change::
      :tags: bug

      The Redis backend now creates a copy of the "arguments" dictionary passed
      to it, before popping values out of it.  This prevents the given
      dictionary from losing its keys.

    .. change::
      :tags: bug
      :tickets: 97

      Fixed bug in "null" backend where :class:`.NullLock` did not
      accept a flag for the :meth:`.NullLock.acquire` method, nor did
      it return a boolean value for "success".

.. changelog::
    :version: 0.5.7
    :released: Mon Oct 19 2015

    .. change::
      :tags: feature
      :pullreq: 37
      :tickets: 54

      Added new parameter :paramref:`.GenericMemcachedBackend.lock_timeout`,
      used in conjunction with
      :paramref:`.GenericMemcachedBackend.distributed_lock`, will specify the
      timeout used when communicating to the ``.add()`` method of the memcached
      client.  Pull request courtesy Frits Stegmann and Morgan Fainberg.

    .. change::
      :tags: feature
      :pullreq: 35
      :tickets: 65

      Added a new flag :paramref:`.CacheRegion.configure.replace_existing_backend`,
      allows a region to have a new backend replace an existing one.
      Pull request courtesy hbccbh.

    .. change::
      :tags: feature, tests
      :pullreq: 33

      Test suite now runs using py.test.  Pull request courtesy
      John Anderson.

    .. change::
      :tags: bug, redis
      :tickets: 74

      Repaired the :meth:`.CacheRegion.get_multi` method when used with a
      list of zero length against the redis backend.

.. changelog::
    :version: 0.5.6
    :released: Mon Feb 2 2015

    .. change::
      :tags: feature
      :pullreq: 30

      Changed the pickle protocol for the file/DBM backend to
      ``pickle.HIGHEST_PROTOCOL`` when producing new pickles,
      to match that of the redis and memorypickle backends.
      Pull request courtesy anentropic.

.. changelog::
    :version: 0.5.5
    :released: Wed Jan 21 2015

    .. change::
      :tags: feature
      :pullreq: 26

      Added new arguments
      :paramref:`.CacheRegion.cache_on_arguments.function_key_generator` and
      :paramref:`.CacheRegion.cache_multi_on_arguments.function_multi_key_generator`
      which serve as per-decorator replacements for the region-wide
      :paramref:`.CacheRegion.function_key_generator` and
      :paramref:`.CacheRegion.function_multi_key_generator` parameters,
      respectively, so that custom key production schemes can be applied
      on a per-function basis within one region.
      Pull request courtesy Hongbin Lu.

    .. change::
      :tags: bug
      :tickets: 71
      :pullreq: 25

      Fixed bug where sending -1 for the
      :paramref:`.CacheRegion.get_or_create.expiration_time` parameter to
      :meth:`.CacheRegion.get_or_create` or
      :meth:`.CacheRegion.get_or_create_multi`
      would fail to honor the setting as "no expiration time".  Pull request
      courtesy Hongbin Lu.

    .. change::
      :tags: bug
      :tickets: 41
      :pullreq: 28

      The ``wrap`` argument is now propagated when calling
      :meth:`.CacheRegion.configure_from_config`.  Pull request courtesy
      Jonathan Vanasco.

    .. change::
      :tags: bug

      Fixed tests under py.test, which were importing a symbol from
      pytest itself ``is_unittest`` which has been removed.

.. changelog::
    :version: 0.5.4
    :released: Sat Jun 14 2014

    .. change::
      :tags: feature
      :pullreq: 18

      Added new :class:`.NullBackend`, for testing and cache-disabling
      purposes.  Pull request courtesy Wichert Akkerman.

    .. change::
      :tags: bug
      :pullreq: 19

      Added missing Mako test dependency to setup.py.
      Pull request courtesy Wichert Akkerman.

    .. change::
      :tags: bug
      :tickets: 58
      :pullreq: 20

      Fixed bug where calling :meth:`.CacheRegion.get_multi` or
      :meth:`.CacheRegion.set_multi` with an empty list would cause failures
      based on backend.  Pull request courtesy Wichert Akkerman.

    .. change::
      :tags: feature
      :pullreq: 17

      Added new :paramref:`.RedisBackend.connection_pool` option
      on the Redis backend; this can be passed a ``redis.ConnectionPool``
      instance directly.  Pull request courtesy Masayuko.

    .. change::
      :tags: feature
      :pullreq: 16

      Added new :paramref:`.RedisBackend.socket_timeout` option
      on the Redis backend.  Pull request courtesy
      Saulius Menkevičius.

    .. change::
      :tags: feature

      Added support for tests to run via py.test.

    .. change::
      :tags: bug
      :pullreq: 15

      Repaired the entry point for Mako templates; the name of the entrypoint
      itself was wrong vs. what was in the docs, but beyond that the entrypoint
      would load the wrong module name.  Pull request courtesy zoomorph.

    .. change::
    	:tags: bug
    	:tickets: 57
    	:pullreq: 13

      The :func:`.coerce_string_conf` function, which is used by
      :meth:`.Region.configure_from_config`, will now recognize floating point
      values when parsing conf strings and deliver them as such; this supports
      non-integer values such as Redis ``lock_sleep``.  Pullreq courtesy
      Jeff Dairiki.

.. changelog::
    :version: 0.5.3
    :released: Wed Jan 8 2014

    .. change::
        :tags: bug
        :pullreq: 10

      Fixed bug where the key_mangler would get in the way of usage of the
      async_creation_runner feature within the :meth:`.Region.get_or_create`
      method, by sending in the mangled key instead of the original key.  The
      "mangled" key is only supposed to be exposed within the backend storage,
      not the creation function which sends the key back into the :meth:`.Region.set`,
      which does the mangling itself.  Pull request courtesy Ryan Kolak.

    .. change::
        :tags: bug, py3k

      Fixed bug where the :meth:`.Region.get_multi` method wasn't calling
      the backend correctly in Py3K (e.g. was passing a destructive ``map()``
      object) which would cause this method to fail on the memcached backend.

    .. change::
        :tags: feature
        :tickets: 55

      Added a ``get()`` method to complement the ``set()``, ``invalidate()``
      and ``refresh()`` methods established on functions decorated by
      :meth:`.CacheRegion.cache_on_arguments` and
      :meth:`.CacheRegion.cache_multi_on_arguments`.  Pullreq courtesy
      Eric Hanchrow.

    .. change::
        :tags: feature
        :tickets: 51
        :pullreq: 11

      Added a new variant on :class:`.MemoryBackend`, :class:`.MemoryPickleBackend`.
      This backend applies ``pickle.dumps()`` and ``pickle.loads()`` to cached
      values upon set and get, so that similar copy-on-cache behavior as that
      of other backends is employed, guarding cached values against subsequent
      in-memory state changes.  Pullreq courtesy Jonathan Vanasco.

    .. change::
        :tags: bug
        :pullreq: 9

      Fixed a format call in the redis backend which would otherwise fail
      on Python 2.6; courtesy Jeff Dairiki.

.. changelog::
    :version: 0.5.2
    :released: Fri Nov 15 2013

    .. change::
        :tags: bug

      Fixes to routines on Windows, including that default unit tests pass,
      and an adjustment to the "soft expiration" feature to ensure the
      expiration works given windows time.time() behavior.

    .. change::
        :tags: bug

      Added py2.6 compatibility for unsupported ``total_seconds()`` call
      in region.py

    .. change::
        :tags: feature
        :tickets: 44

      Added a new argument ``lock_factory`` to the :class:`.DBMBackend`
      implementation.  This allows for drop-in replacement of the default
      :class:`.FileLock` backend, which builds on ``os.flock()`` and only
      supports Unix platforms.  A new abstract base :class:`.AbstractFileLock`
      has been added to provide a common base for custom lock implementations.
      The documentation points to an example thread-based rw lock which is
      now tested on Windows.

.. changelog::
    :version: 0.5.1
    :released: Thu Oct 10 2013

    .. change::
        :tags: feature
        :tickets: 38

      The :meth:`.CacheRegion.invalidate` method now supports an option
      ``hard=True|False``.  A "hard" invalidation, equivalent to the
      existing functionality of :meth:`.CacheRegion.invalidate`, means
      :meth:`.CacheRegion.get_or_create` will not return the "old" value at
      all, forcing all getters to regenerate or wait for a regeneration.
      "soft" invalidation means that getters can continue to return the
      old value until a new one is generated.

    .. change::
        :tags: feature
        :tickets: 40

      New dogpile-specific exception classes have been added, so that
      issues like "region already configured", "region unconfigured",
      raise dogpile-specific exceptions.  Other exception classes have
      been made more specific.  Also added new accessor
      :attr:`.CacheRegion.is_configured`. Pullreq courtesy Morgan Fainberg.

    .. change::
        :tags: bug

      Erroneously missed when the same change was made for ``set()``
      in 0.5.0, the Redis backend now uses ``pickle.HIGHEST_PROTOCOL``
      for the ``set_multi()`` method as well when producing pickles.
      Courtesy Łukasz Fidosz.

    .. change::
        :tags: bug, redis, py3k
        :tickets: 39

      Fixed an errant ``u''`` causing incompatibility in Python3.2
      in the Redis backend, courtesy Jimmey Mabey.

    .. change::
        :tags: bug

      The :func:`.util.coerce_string_conf` method now correctly coerces
      negative integers and those with a leading + sign. This previously
      prevented configuring a :class:`.CacheRegion` with an ``expiration_time``
      of ``'-1'``. Courtesy David Beitey.

    .. change::
        :tags: bug

      The ``refresh()`` method on :meth:`.CacheRegion.cache_multi_on_arguments`
      now supports the ``asdict`` flag.

.. changelog::
    :version: 0.5.0
    :released: Fri Jun 21 2013

    .. change::
        :tags: misc

      Source repository has been moved to git.

    .. change::
        :tags: bug

      The Redis backend now uses ``pickle.HIGHEST_PROTOCOL`` when
      producing pickles.  Courtesy Lx Yu.

    .. change::
        :tags: bug

      :meth:`.CacheRegion.cache_on_arguments` now has a new argument
      ``to_str``, defaults to ``str()``.  Can be replaced with ``unicode()``
      or other functions to support caching of functions that
      accept non-unicode arguments.  Initial patch courtesy Lx Yu.

    .. change::
        :tags: feature

      Now using the ``Lock`` included with the Python
      ``redis`` backend, which adds ``lock_timeout``
      and ``lock_sleep`` arguments to the :class:`.RedisBackend`.

    .. change::
        :tags: feature
        :tickets: 33, 35

      Added new methods :meth:`.CacheRegion.get_or_create_multi`
      and :meth:`.CacheRegion.cache_multi_on_arguments`, which
      make use of the :meth:`.CacheRegion.get_multi` and similar
      functions to store and retrieve multiple keys at once while
      maintaining dogpile semantics for each.

    .. change::
      :tags: feature
      :tickets: 36

      Added a method ``refresh()`` to functions decorated by
      :meth:`.CacheRegion.cache_on_arguments` and
      :meth:`.CacheRegion.cache_multi_on_arguments`, to complement
      ``invalidate()`` and ``set()``.

    .. change::
        :tags: feature
        :tickets: 13

      :meth:`.CacheRegion.configure` accepts an
      optional ``datetime.timedelta`` object
      for the ``expiration_time`` argument as well
      as an integer, courtesy Jack Lutz.

    .. change::
        :tags: feature
        :tickets: 20

      The ``expiration_time`` argument passed to
      :meth:`.CacheRegion.cache_on_arguments`
      may be a callable, to return a dynamic
      timeout value.  Courtesy David Beitey.

    .. change::
        :tags: feature
        :tickets: 26

      Added support for simple augmentation of existing
      backends using the :class:`.ProxyBackend` class.
      Thanks to Tim Hanus for the great effort with
      development, testing, and documentation.

    .. change::
        :tags: feature
        :pullreq: 14

      Full support for multivalue get/set/delete
      added, using :meth:`.CacheRegion.get_multi`,
      :meth:`.CacheRegion.set_multi`, :meth:`.CacheRegion.delete_multi`,
      courtesy Marcos Araujo Sobrinho.

    .. change::
        :tags: bug
        :tickets: 27

      Fixed bug where the "name" parameter for
      :class:`.CacheRegion` was ignored entirely.
      Courtesy Wichert Akkerman.

.. changelog::
    :version: 0.4.3
    :released: Thu Apr 4 2013

    .. change::
        :tags: bug

      Added support for the ``cache_timeout`` Mako
      argument to the Mako plugin, which will pass
      the value to the ``expiration_time`` argument
      of :meth:`.CacheRegion.get_or_create`.

    .. change::
        :tags: feature
        :pullreq: 13

      :meth:`.CacheRegion.get_or_create` and
      :meth:`.CacheRegion.cache_on_arguments` now accept a new
      argument ``should_cache_fn``, receives the value
      returned by the "creator" and then returns True or
      False, where True means "cache plus return",
      False means "return the value but don't cache it."

.. changelog::
    :version: 0.4.2
    :released: Sat Jan 19 2013

    .. change::
        :tags: feature
        :pullreq: 10

      An "async creator" function can be specified to
      :class:`.CacheRegion` which allows the "creation" function
      to be called asynchronously or be subsituted for
      another asynchronous creation scheme.  Courtesy
      Ralph Bean.

.. changelog::
    :version: 0.4.1
    :released: Sat Dec 15 2012

    .. change::
        :tags: feature
        :pullreq: 9

      The function decorated by :meth:`.CacheRegion.cache_on_arguments`
      now includes a ``set()`` method, in addition to the existing
      ``invalidate()`` method.   Like ``invalidate()``, it accepts
      a set of function arguments, but additionally accepts as the
      first positional argument a new value to place in the cache,
      to take the place of that key.  Courtesy Antoine Bertin.

    .. change::
        :tags: bug
        :tickets: 15

      Fixed bug in DBM backend whereby if an error occurred
      during the "write" operation, the file lock, if enabled,
      would not be released, thereby deadlocking the app.

    .. change::
        :tags: bug
        :tickets: 12

      The :func:`.util.function_key_generator` used by the
      function decorator no longer coerces non-unicode
      arguments into a Python unicode object on Python 2.x;
      this causes failures on backends such as DBM which
      on Python 2.x apparently require bytestrings.  The
      key_mangler is still needed if actual unicode arguments
      are being used by the decorated function, however.

    .. change::
        :tags: feature

      Redis backend now accepts optional "url" argument,
      will be passed to the new ``StrictRedis.from_url()``
      method to determine connection info.  Courtesy
      Jon Rosebaugh.

    .. change::
        :tags: feature

      Redis backend now accepts optional "password"
      argument.  Courtesy Jon Rosebaugh.

    .. change::
        :tags: feature

      DBM backend has "fallback" when calling dbm.get() to
      instead use dictionary access + KeyError, in the case
      that the "gdbm" backend is used which does not include
      .get().  Courtesy Jon Rosebaugh.

.. changelog::
    :version: 0.4.0
    :released: Tue Oct 30 2012

    .. change::
        :tags: bug
        :tickets: 1

      Using dogpile.core 0.4.0 now, fixes a critical
      bug whereby dogpile pileup could occur on first value
      get across multiple processes, due to reliance upon
      a non-shared creation time.  This is a dogpile.core
      issue.

    .. change::
        :tags: bug
        :tickets:

      Fixed missing __future__ with_statement
      directive in region.py.

.. changelog::
    :version: 0.3.1
    :released: Tue Sep 25 2012

    .. change::
        :tags: bug
        :tickets:

      Fixed the mako_cache plugin which was not yet
      covered, and wasn't implementing the mako plugin
      API correctly; fixed docs as well.  Courtesy
      Ben Hayden.

    .. change::
        :tags: bug
        :tickets:

      Fixed setup so that the tests/* directory
      isn't yanked into the install.  Courtesy Ben Hayden.

.. changelog::
    :version: 0.3.0
    :released: Thu Jun 14 2012

    .. change::
        :tags: feature
        :tickets:

      get() method now checks expiration time
      by default.   Use ignore_expiration=True
      to bypass this.

    .. change::
        :tags: feature
        :tickets: 7

      Added new invalidate() method.  Sets the current
      timestamp as a minimum value that all retrieved
      values must be created after.  Is honored by the
      get_or_create() and get() methods.

    .. change::
        :tags: bug
        :tickets: 8

      Fixed bug whereby region.get() didn't
      work if the value wasn't present.



.. changelog::
    :version: 0.2.4
    :released:

    .. change::
        :tags:
        :tickets:

      Fixed py3k issue with config string coerce,
      courtesy Alexander Fedorov

.. changelog::
    :version: 0.2.3
    :released: Wed May 16 2012

    .. change::
        :tags:
        :tickets: 3

      support "min_compress_len" and "memcached_expire_time"
      with python-memcached backend.  Tests courtesy
      Justin Azoff

    .. change::
        :tags:
        :tickets: 4

      Add support for coercion of string config values
      to Python objects - ints, "false", "true", "None".

    .. change::
        :tags:
        :tickets: 5

      Added support to DBM file lock to allow reentrant
      access per key within a single thread, so that
      even though the DBM backend locks for the whole file,
      a creation function that calls upon a different
      key in the cache can still proceed.

    .. change::
        :tags:
        :tickets:

      Fixed DBM glitch where multiple readers
      could be serialized.

    .. change::
        :tags:
        :tickets:

      Adjust bmemcached backend to work with newly-repaired
      bmemcached calling API (see bmemcached
      ef206ed4473fec3b639e).

.. changelog::
    :version: 0.2.2
    :released: Thu Apr 19 2012

    .. change::
        :tags:
        :tickets:

      add Redis backend, courtesy Ollie Rutherfurd

.. changelog::
    :version: 0.2.1
    :released: Sun Apr 15 2012

    .. change::
        :tags:
        :tickets:

      move tests into tests/cache namespace

    .. change::
        :tags:
        :tickets:

      py3k compatibility is in-place now, no
      2to3 needed.

.. changelog::
    :version: 0.2.0
    :released: Sat Apr 14 2012

    .. change::
        :tags:
        :tickets:

      Based on dogpile.core now, to get the package
      namespace thing worked out.



.. changelog::
    :version: 0.1.1
    :released: Tue Apr 10 2012

    .. change::
        :tags:
        :tickets:

      Fixed the configure_from_config() method of region
      and backend which wasn't working.  Courtesy
      Christian Klinger.

.. changelog::
    :version: 0.1.0
    :released: Sun Apr 08 2012

    .. change::
        :tags:
        :tickets:

       Initial release.

    .. change::
        :tags:
        :tickets:

       Includes a pylibmc backend and a plain dictionary backend.

