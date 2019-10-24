.. change::
    :tags: feature

    Added logging facililities into :class:`.CacheRegion`, to indicate key
    events such as cache keys missing or regeneration of values.  As these can
    be very high volume log messages, ``logging.DEBUG`` is used as the log
    level for the events.  Pull request courtesy Stéphane Brunner.


