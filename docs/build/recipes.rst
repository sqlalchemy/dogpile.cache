Recipes
=======

Invalidating a group of related keys
-------------------------------------

This recipe presents a way to track the cache keys related to a particular region,
for the purposes of invalidating a series of keys that relate to a particular id.

Three cached functions, ``user_fn_one()``, ``user_fn_two()``, ``user_fn_three()``
each perform a different function based on a ``user_id`` integer value.  The
region applied to cache them uses a custom key generator which tracks each cache
key generated, pulling out the integer "id" and replacing with a template.

When all three functions have been called, the key generator is now aware of
these three keys:  ``user_fn_one_%d``, ``user_fn_two_%d``, and
``user_fn_three_%d``.   The ``invalidate_user_id()`` function then knows that
for a particular ``user_id``, it needs to hit all three of those keys
in order to invalidate everything having to do with that id.

::

  from dogpile.cache import make_region
  from itertools import count

  user_keys = set()
  def my_key_generator(namespace, fn):
      fname = fn.__name__
      def generate_key(*arg):
          # generate a key template:
          # "fname_%d_arg1_arg2_arg3..."
          key_template = fname + "_" + \
                              "%d" + \
                              "_".join(str(s) for s in arg[1:])

          # store key template
          user_keys.add(key_template)

          # return cache key
          user_id = arg[0]
          return key_template % user_id

      return generate_key

  def invalidate_user_id(region, user_id):
      for key in user_keys:
          region.delete(key % user_id)

  region = make_region(
      function_key_generator=my_key_generator
      ).configure(
          "dogpile.cache.memory"
      )

  counter = count()

  @region.cache_on_arguments()
  def user_fn_one(user_id):
      return "user fn one: %d, %d" % (next(counter), user_id)

  @region.cache_on_arguments()
  def user_fn_two(user_id):
      return "user fn two: %d, %d" % (next(counter), user_id)

  @region.cache_on_arguments()
  def user_fn_three(user_id):
      return "user fn three: %d, %d" % (next(counter), user_id)

  print user_fn_one(5)
  print user_fn_two(5)
  print user_fn_three(7)
  print user_fn_two(7)

  invalidate_user_id(region, 5)
  print "invalidated:"
  print user_fn_one(5)
  print user_fn_two(5)
  print user_fn_three(7)
  print user_fn_two(7)


Asynchronous Data Updates with ORM Events
-----------------------------------------

This recipe presents one technique of optimistically pushing new data
into the cache when an update is sent to a database.

Using SQLAlchemy for database querying, suppose a simple cache-decorated
function returns the results of a database query::

    @region.cache_on_arguments()
    def get_some_data(argument):
        # query database to get data
        data = Session().query(DBClass).filter(DBClass.argument == argument).all()
        return data

We would like this particular function to be re-queried when the data
has changed.  We could call ``get_some_data.invalidate(argument, hard=False)``
at the point at which the data changes, however this only
leads to the invalidation of the old value; a new value is not generated until
the next call, and also means at least one client has to block while the
new value is generated.    We could also call
``get_some_data.refresh(argument)``, which would perform the data refresh
at that moment, but then the writer is delayed by the re-query.

A third variant is to instead offload the work of refreshing for this query
into a background thread or process.   This can be acheived using
a system such as the :paramref:`.CacheRegion.async_creation_runner`.
However, an expedient approach for smaller use cases is to link cache refresh
operations to the ORM session's commit, as below::

    from sqlalchemy import event
    from sqlalchemy.orm import Session

    def cache_refresh(session, refresher, *args, **kwargs):
        """
        Refresh the functions cache data in a new thread. Starts refreshing only
        after the session was committed so all database data is available.
        """
        assert isinstance(session, Session), \
            "Need a session, not a sessionmaker or scoped_session"

        @event.listens_for(session, "after_commit")
        def do_refresh(session):
            t = Thread(target=refresher, args=args, kwargs=kwargs)
            t.daemon = True
            t.start()

Within a sequence of data persistence, ``cache_refresh`` can be called
given a particular SQLAlchemy ``Session`` and a callable to do the work::

    def add_new_data(session, argument):
        # add some data
        session.add(something_new(argument))

        # add a hook to refresh after the Session is committed.
        cache_refresh(session, get_some_data.refresh, argument)

Note that the event to refresh the data is associated with the ``Session``
being used for persistence; however, the actual refresh operation is called
with a **different** ``Session``, typically one that is local to the refresh
operation, either through a thread-local registry or via direct instantiation.


Prefixing all keys in Redis
---------------------------

If you use a redis instance as backend that contains other keys besides the ones
set by dogpile.cache, it is a good idea to uniquely prefix all dogpile.cache
keys, to avoid potential collisions with keys set by your own code.  This can
easily be done using a key mangler function::

    from dogpile.cache import make_region

    region = make_region(
      key_mangler=lambda key: "myapp:dogpile:" + key
    )


Encoding/Decoding data into another format
------------------------------------------

.. sidebar:: A Note on Data Encoding

    Under the hood, dogpile.cache wraps cached data in an instance of
    ``dogpile.cache.api.CachedValue`` and then pickles that data for storage
    along with some bookkeeping metadata. If you implement a ProxyBackend to
    encode/decode data, that transformation will happen on the pre-pickled data-
    dogpile does not store the data 'raw' and will still pass a pickled payload
    to the backend.  This behavior can negate the hopeful improvements of some
    encoding schemes.

Since dogpile is managing cached data, you may be concerned with the size of
your payloads.  A possible method of helping minimize payloads is to use a
ProxyBackend to recode the data on-the-fly or otherwise transform data as it
enters or leaves persistent storage.

In the example below, we define 2 classes to implement msgpack encoding.  Msgpack
(http://msgpack.org/) is a serialization format that works exceptionally well
with json-like data and can serialize nested dicts into a much smaller payload
than Python's own pickle.  ``_EncodedProxy`` is our base class
for building data encoders, and inherits from dogpile's own `ProxyBackend`.  You
could just use one class.  This class passes 4 of the main `key/value` functions
into a configurable decoder and encoder.  The ``MsgpackProxy`` class simply
inherits from ``_EncodedProxy`` and  implements the necessary ``value_decode``
and ``value_encode`` functions.


Encoded ProxyBackend Example::

    from dogpile.cache.proxy import ProxyBackend
    import msgpack

    class _EncodedProxy(ProxyBackend):
        """base class for building value-mangling proxies"""

        def value_decode(self, value):
            raise NotImplementedError("override me")

        def value_encode(self, value):
            raise NotImplementedError("override me")

        def set(self, k, v):
            v = self.value_encode(v)
            self.proxied.set(k, v)

        def get(self, key):
            v = self.proxied.get(key)
            return self.value_decode(v)

        def set_multi(self, mapping):
            """encode to a new dict to preserve unencoded values in-place when
               called by `get_or_create_multi`
               """
            mapping_set = {}
            for (k, v) in mapping.iteritems():
                mapping_set[k] = self.value_encode(v)
            return self.proxied.set_multi(mapping_set)

        def get_multi(self, keys):
            results = self.proxied.get_multi(keys)
            translated = []
            for record in results:
                try:
                    translated.append(self.value_decode(record))
                except Exception as e:
                    raise
            return translated


    class MsgpackProxy(_EncodedProxy):
        """custom decode/encode for value mangling"""

        def value_decode(self, v):
            if not v or v is NO_VALUE:
                return NO_VALUE
            # you probably want to specify a custom decoder via `object_hook`
            v = msgpack.unpackb(payload, encoding="utf-8")
            return CachedValue(*v)

        def value_encode(self, v):
            # you probably want to specify a custom encoder via `default`
            v = msgpack.packb(payload, use_bin_type=True)
            return v

    # extend our region configuration from above with a 'wrap'
    region = make_region().configure(
        'dogpile.cache.pylibmc',
        expiration_time = 3600,
        arguments = {
            'url': ["127.0.0.1"],
        },
        wrap = [MsgpackProxy, ]
    )
