.. change::
    :tags: usecase, memcached

    Added support for additional pymemcache ``HashClient`` parameters
    ``retry_attempts``, ``retry_timeout``, and
    ``dead_timeout``.

    .. seealso::

        :paramref:`.PyMemcacheBackend.hashclient_retry_attempts`

        :paramref:`.PyMemcacheBackend.hashclient_retry_timeout`

        :paramref:`.PyMemcacheBackend.dead_timeout`