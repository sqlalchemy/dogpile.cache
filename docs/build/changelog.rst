==============
Changelog
==============
.. changelog::
    :version: 0.4.2
    :released: Sat Jan 19 2013

    .. change::
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

