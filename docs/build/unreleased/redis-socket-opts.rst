.. change::
    :tags: usecase, redis
    :tickets: 252

    Added support for additional Redis client parameters
    :paramref:`.RedisBackend.socket_connect_timeout`,
    :paramref:`.RedisBackend.socket_keepalive` and
    :paramref:`.RedisBackend.socket_keepalive_options`. Pull request courtesy
    Takashi Kajinami.
