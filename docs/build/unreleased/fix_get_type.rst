.. change::
    :tags: bug, typing

    Fixed the return type for :meth:`.CacheRegion.get`, which was inadvertently
    hardcoded to use ``CacheReturnType`` that only resolved to ``CachedValue``
    or ``NoValue``.   Fixed to return ``ValuePayload`` which resolves to
    ``Any``, as well as a new literal indicating an enum constant for
    :data:`.api.NO_VALUE`.  The :data:`.api.NO_VALUE` constant remains
    available as the single element of this enum.
