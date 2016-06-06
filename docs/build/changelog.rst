==============
Changelog
==============
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

