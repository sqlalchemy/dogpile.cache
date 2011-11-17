.. note:: dogpile.cache is **not released or completed** at this time.   Development
   is currently in progress and the current code is not yet functional.

Introduction
============

At its core, Dogpile provides a locking interface around a "value creation" function.

The interface supports several levels of usage, starting from
one that is very rudimentary, then providing more intricate 
usage patterns to deal with certain scenarios.  The documentation here will attempt to 
provide examples that use successively more and more of these features, as 
we approach how a fully featured caching system might be constructed around
Dogpile.

Note that when using the `dogpile.cache <http://bitbucket.org/zzzeek/dogpile.cache>`_
package, the constructs here provide the internal implementation for that system,
and users of that system don't need to access these APIs directly (though understanding
the general patterns is a terrific idea in any case).
Using the core Dogpile APIs described here directly implies you're building your own 
resource-usage system outside, or in addition to, the one 
`dogpile.cache <http://bitbucket.org/zzzeek/dogpile.cache>`_ provides.

Usage
=====

A dogpile.cache configuration consists of the following components:

* A *region*, which is an instance of ``CacheRegion``, and defines the configuration
  details for a particular cache backend.
* A *backend*, which is an instance of ``CacheBackend``, describing how values
  are stored and retrieved from a backend.  This interface specifies only
  ``get()``, ``put()`` and ``delete()``.
* Value generation functions.   These are user-defined functions that generate
  new values to be placed in the cache.

The most common caching style in use these days is via memcached, so an example
of this using the `pylibmc <http://pypi.python.org/pypi/pylibmc>`_ backend looks like::

    from dogpile.cache import make_region

    region = make_region().configure(
        'dogpile.cache.pylibmc',
        expiration_time = 3600,
        arguments = {
            'url':["127.0.0.1"],
            'binary':True,
            'behaviors':{"tcp_nodelay": True,"ketama":True}
        }
    )

    @region.cache_on_arguments
    def load_user_info(user_id):
        return some_database.lookup_user_by_id(user_id)

Above, we create a ``CacheRegion`` using the ``make_region()`` function, then
apply the backend configuration via the ``configure()`` method, which returns the 
region.  The name of the backend is the only required argument,
in this case ``dogpile.cache.pylibmc``.

Subsequent arguments then include *expiration_time*, which is the expiration 
time passed to the Dogpile lock, and *arguments*, which are arguments used directly
by the backend - in this case we are using arguments that are passed directly
to the pylibmc module.

Backends
========

Backends are located using the setuptools entrypoint system.  To make life easier
for writers of ad-hoc backends, a helper function is included which registers any
backend in the same way as if it were part of the existing sys.path.

For example, to create a backend called ``DictionaryBackend``, we subclass
``CacheBackend``::

    from dogpile.cache import CacheBackend, NO_VALUE

    class DictionaryBackend(CacheBackend):
        def __init__(self, arguments):
            self.cache = {}

        def get(self, key):
            return self.cache.get(key, NO_VALUE)

        def put(self, key, value):
            self.cache[key] = value

        def delete(self, key):
            self.cache.pop(key)

Then make sure the class is available underneath the entrypoint
``dogpile.cache``.  If we did this in a ``setup.py`` file, it would be 
in ``setup()`` as::

    entry_points="""
      [dogpile.cache]
      dictionary = mypackage.mybackend:DictionaryBackend
      """

Alternatively, if we want to register the plugin in the same process 
space without bothering to install anything, we can use ``register_backend``::

    from dogpile.cache import register_backend

    register_backend("dictionary", "mypackage.mybackend", "DictionaryBackend")

Our new backend would be usable in a region like this::

    from dogpile.cache import make_region

    region = make_region("dictionary")

    data = region.put("somekey", "somevalue")

The values we receive for the backend here are instances of
``CachedValue``.  This is a tuple subclass of length two, of the form::

    (payload, metadata)

Where "payload" is the thing being cached, and "metadata" is information
we store in the cache - a dictionary which currently has just the "creation time"
and a "version identifier" as key/values.  If the cache backend requires serialization, 
pickle or similar can be used on the tuple - the "metadata" portion will always
be a small and easily serializable Python structure.

Region Arguments
================

The ``make_region()`` function accepts these arguments:

``name``

  Optional.  A string name for the region.  This isn't used internally
  but can be accessed via the ``.name`` parameter, helpful
  for configuring a region from a config file.

``function_key_generator``

  Optional.  Plug in a function that will produce a "cache key" given 
  a data creation function and arguments.   The structure of this function
  should be two levels: given the data creation function, return a new
  function that generates the key based on the given arguments.  Such
  as::

    def my_key_generator(fn):
        namespace = fn.__name__
        def generate_key(*arg):
            return namespace + "_".join(str(s) for s in arg)
        return generate_key


    region = make_region(
        function_key_generator = my_key_generator
    ).configure(
        "dogpile.cache.dbm",
        expiration_time=300,
        arguments={
            "filename":"file.dbm"
        }
    )

``key_mangler``

  Optional.  Function which will "mangle" the incoming keys.  If left
  at ``None``, the backend may provide a default "mangler" function.
  Set to ``False`` to unconditionally disable key mangling.

One you have a ``CacheRegion``, the ``cache_on_arguments()`` method can
be used to decorate functions, but the cache itself can't be used until
``configure()`` is called.  That method accepts these arguments:

``backend``
  Required.  This is the name of the ``CacheBackend`` to use, and
  is resolved by loading the class from the ``dogpile.cache`` entrypoint.

``expiration_time``

  Optional.  The expiration time passed to the dogpile system.  The ``get_or_create()``
  method as well as the ``cache_on_arguments()`` decorator (note:  **not** the
  ``get()`` method) will call upon the value creation function after this
  time period has passed since the last generation.

``arguments``

  Optional.  The structure here is passed directly to the constructor
  of the ``CacheBackend`` in use, though is typically a dictionary.

Configure Region from a Configuration Dictionary
================================================

Call ``configure_from_config()`` instead::

    local_region = make_region()
    memcached_region = make_region()

    # regions are ready to use for function
    # decorators, but not yet for actual caching

    # later, when config is available
    myconfig = {
        "cache.local.backend":"dogpile.cache.dbm",
        "cache.local.arguments.filename":"/path/to/dbmfile.dbm",
        "cache.memcached.backend":"dogpile.cache.pylibmc",
        "cache.memcached.arguments.url":"127.0.0.1, 10.0.0.1",
    }
    local_region.configure_from_config(myconfig, "cache.local.")
    memcached_region.configure_from_config(myconfig, "cache.memcached.")

Using a Region
==============

The ``CacheRegion`` object is our front-end interface to a cache.  It includes
the following methods:

``get(key)``

  Return a value from the cache, based on the given key.  While it's typical
  the key is a string, it's passed through to the underlying backend so can
  be of any type recognized by the backend.  If the value is not present, returns the 
  token ``NO_VALUE``.  ``NO_VALUE`` evaluates to False, but is separate
  from ``None`` to distinguish between a cached value of ``None``.
  Note that the ``expiration_time`` argument is **not** used here - this method
  is a direct line to the backend's behavior.

``get_or_create(key, creator)``

  Similar to ``get``, will use the given "creation" function to create a new
  value if the value does not exist.   This will use the underlying dogpile/
  expiration mechanism to determine when/how the creation function is called.

``put(key, value)``

  Place a new value in the cache under the given key.

``delete(key)``

  Remove a value from the cache.   This operation is idempotent (can be
  called multiple times, or on a non-existent key, safely)

``cache_on_arguments(fn)``

  A function decorator that will cache the return value of the function
  using a key derived from the name of the function, its location within
  the application (i.e. source filename) as well as the arguments
  passed to the function.

  The generation of the key from the function is the big 
  controversial thing that was a source of user issues with Beaker.  Dogpile
  provides the latest and greatest algorithm used by Beaker, but also
  allows you to use whatever function you want, by specifying it
  to ``make_region()`` using the ``function_key_generator`` argument.


Mako Integration
================

dogpile.cache includes a Mako plugin that replaces Beaker as the cache backend.
Simply setup a Mako template lookup using the "dogpile.cache" cache implementation
and a region dictionary::

    from dogpile.cache import make_region
    from mako.lookup import TemplateLookup

    my_regions = {
        "local":make_region(
                    "dogpile.cache.dbm", 
                    expiration_time=360,
                    arguments={"filename":"file.dbm"}
                ),
        "memcached":make_region(
                    "dogpile.cache.pylibmc", 
                    expiration_time=3600,
                    arguments={"url":["127.0.0.1"]}
                )
    }

    mako_lookup = TemplateLookup(
        directories=["/myapp/templates"],
        cache_impl="dogpile.cache",
        cache_regions=my_regions
    )

To use the above configuration in a template, use the ``cached=True`` argument on any
Mako tag which accepts it, in conjunction with the name of the desired region
as the ``cache_region`` argument::

    <%def name="mysection()" cached=True cache_region="memcached">
        some content that's cached
    </%def>
