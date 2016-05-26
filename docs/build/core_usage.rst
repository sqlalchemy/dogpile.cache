============
dogpile Core
============

``dogpile`` provides a locking interface around a "value creation" and
"value retrieval" pair of functions.

.. versionchanged:: 0.6.0  The ``dogpile`` package encapsulates the
   functionality that was previously provided by the separate
   ``dogpile.core`` package.

The primary interface is the :class:`.Lock` object, which provides for
the invocation of the creation function by only one thread and/or process at
a time, deferring all other threads/processes to the "value retrieval" function
until the single creation thread is completed.

Do I Need to Learn the dogpile Core API Directly?
=================================================

It's anticipated that most users of ``dogpile`` will be using it indirectly
via the ``dogpile.cache`` caching
front-end.  If you fall into this category, then the short answer is no.

Using the core ``dogpile`` APIs described here directly implies you're building your own
resource-usage system outside, or in addition to, the one
``dogpile.cache`` provides.

Rudimentary Usage
==================

The primary API dogpile provides is the :class:`.Lock` object.   This object allows for
functions that provide mutexing, value creation, as well as value retrieval.

An example usage is as follows::

  from dogpile import Lock, NeedRegenerationException
  import threading
  import time

  # store a reference to a "resource", some
  # object that is expensive to create.
  the_resource = [None]

  def some_creation_function():
      # call a value creation function
      value = create_some_resource()

      # get creationtime using time.time()
      creationtime = time.time()

      # keep track of the value and creation time in the "cache"
      the_resource[0] = tup = (value, creationtime)

      # return the tuple of (value, creationtime)
      return tup

  def retrieve_resource():
      # function that retrieves the resource and
      # creation time.

      # if no resource, then raise NeedRegenerationException
      if the_resource[0] is None:
          raise NeedRegenerationException()

      # else return the tuple of (value, creationtime)
      return the_resource[0]

  # a mutex, which needs here to be shared across all invocations
  # of this particular creation function
  mutex = threading.Lock()

  with Lock(mutex, some_creation_function, retrieve_resource, 3600) as value:
        # some function that uses
        # the resource.  Won't reach
        # here until some_creation_function()
        # has completed at least once.
        value.do_something()

Above, ``some_creation_function()`` will be called
when :class:`.Lock` is first invoked as a context manager.   The value returned by this
function is then passed into the ``with`` block, where it can be used
by application code.  Concurrent threads which
call :class:`.Lock` during this initial period
will be blocked until ``some_creation_function()`` completes.

Once the creation function has completed successfully the first time,
new calls to :class:`.Lock` will call ``retrieve_resource()``
in order to get the current cached value as well as its creation
time; if the creation time is older than the current time minus
an expiration time of 3600, then ``some_creation_function()``
will be called again, but only by one thread/process, using the given
mutex object as a source of synchronization.  Concurrent threads/processes
which call :class:`.Lock` during this period will fall through,
and not be blocked; instead, the "stale" value just returned by
``retrieve_resource()`` will continue to be returned until the creation
function has finished.

The :class:`.Lock` API is designed to work with simple cache backends
like Memcached.   It addresses such issues as:

* Values can disappear from the cache at any time, before our expiration
  time is reached.  The :class:`.NeedRegenerationException` class is used
  to alert the :class:`.Lock` object that a value needs regeneration ahead
  of the usual expiration time.
* There's no function in a Memcached-like system to "check" for a key without
  actually retrieving it.  The usage of the ``retrieve_resource()`` function
  allows that we check for an existing key and also return the existing value,
  if any, at the same time, without the need for two separate round trips.
* The "creation" function used by :class:`.Lock` is expected to store the
  newly created value in the cache, as well as to return it.   This is also
  more efficient than using two separate round trips to separately store,
  and re-retrieve, the object.

.. _caching_decorator:

Example: Using dogpile directly for Caching
===========================================

The following example approximates Beaker's "cache decoration" function, to
decorate any function and store the value in Memcached.   Note that
normally, **we'd just use dogpile.cache here**, however for the purposes
of example, we'll illustrate how the :class:`.Lock` object is used
directly.

We create a Python decorator function called ``cached()`` which will provide
caching for the output of a single function.  It's given the "key" which we'd
like to use in Memcached, and internally it makes usage of :class:`.Lock`,
along with a thread based mutex (we'll see a distributed mutex in the next
section)::

    import pylibmc
    import threading
    import time
    from dogpile import Lock, NeedRegenerationException

    mc_pool = pylibmc.ThreadMappedPool(pylibmc.Client("localhost"))

    def cached(key, expiration_time):
        """A decorator that will cache the return value of a function
        in memcached given a key."""

        mutex = threading.Lock()

        def get_value():
             with mc_pool.reserve() as mc:
                value_plus_time = mc.get(key)
                if value_plus_time is None:
                    raise NeedRegenerationException()
                # return a tuple (value, createdtime)
                return value_plus_time

        def decorate(fn):
            def gen_cached():
                value = fn()
                with mc_pool.reserve() as mc:
                    # create a tuple (value, createdtime)
                    value_plus_time = (value, time.time())
                    mc.put(key, value_plus_time)
                return value_plus_time

            def invoke():
                with Lock(mutex, gen_cached, get_value, expiration_time) as value:
                    return value
            return invoke

        return decorate

Using the above, we can decorate any function as::

    @cached("some key", 3600)
    def generate_my_expensive_value():
        return slow_database.lookup("stuff")

The :class:`.Lock` object will ensure that only one thread at a time performs
``slow_database.lookup()``, and only every 3600 seconds, unless Memcached has
removed the value, in which case it will be called again as needed.

In particular, dogpile.core's system allows us to call the memcached get()
function at most once per access, instead of Beaker's system which calls it
twice, and doesn't make us call get() when we just created the value.

For the mutex object, we keep a ``threading.Lock`` object that's local
to the decorated function, rather than using a global lock.   This localizes
the in-process locking to be local to this one decorated function.   In the next section,
we'll see the usage of a cross-process lock that accomplishes this differently.

Using a File or Distributed Lock with Dogpile
==============================================

The examples thus far use a ``threading.Lock()`` object for synchronization.
If our application uses multiple processes, we will want to coordinate creation
operations not just on threads, but on some mutex that other processes can access.

In this example we'll use a file-based lock as provided by the `lockfile
<http://pypi.python.org/pypi/lockfile>`_ package, which uses a unix-symlink
concept to provide a filesystem-level lock (which also has been made
threadsafe).  Another strategy may base itself directly off the Unix
``os.flock()`` call, or use an NFS-safe file lock like `flufl.lock
<http://pypi.python.org/pypi/flufl.lock>`_, and still another approach is to
lock against a cache server, using a recipe such as that described at `Using
Memcached as a Distributed Locking Service <http://www.regexprn.com/2010/05
/using-memcached-as-distributed-locking.html>`_.

What all of these locking schemes have in common is that unlike the Python
``threading.Lock`` object, they all need access to an actual key which acts as
the symbol that all processes will coordinate upon.   So here, we will also
need to create the "mutex" which we pass to :class:`.Lock` using the ``key``
argument::

    import lockfile
    import os
    from hashlib import sha1

    # ... other imports and setup from the previous example

    def cached(key, expiration_time):
        """A decorator that will cache the return value of a function
        in memcached given a key."""

        lock_path = os.path.join("/tmp", "%s.lock" % sha1(key).hexdigest())

        # ... get_value() from the previous example goes here

        def decorate(fn):
            # ... gen_cached() from the previous example goes here

            def invoke():
                # create an ad-hoc FileLock
                mutex = lockfile.FileLock(lock_path)

                with Lock(mutex, gen_cached, get_value, expiration_time) as value:
                    return value
            return invoke

        return decorate

For a given key "some_key", we generate a hex digest of the key,
then use ``lockfile.FileLock()`` to create a lock against the file
``/tmp/53def077a4264bd3183d4eb21b1f56f883e1b572.lock``.   Any number of :class:`.Lock`
objects in various processes will now coordinate with each other, using this common
filename as the "baton" against which creation of a new value proceeds.

Unlike when we used ``threading.Lock``, the file lock is ultimately locking
on a file, so multiple instances of ``FileLock()`` will all coordinate on
that same file - it's often the case that file locks that rely upon ``flock()``
require non-threaded usage, so a unique filesystem lock per thread is often a good
idea in any case.

