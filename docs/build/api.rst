===
API
===


Region
======

.. automodule:: dogpile.cache.region
    :members:

.. autofunction:: dogpile.cache.util.function_key_generator

Backend API
=============

See the section :ref:`creating_backends` for details on how to
register new backends or :ref:`changing_backend_behavior` for details on
how to alter the behavior of existing backends.

.. automodule:: dogpile.cache.api
    :members:


Backends
==========

.. automodule:: dogpile.cache.backends.memory
    :members:

.. automodule:: dogpile.cache.backends.memcached
    :members:

.. automodule:: dogpile.cache.backends.redis
    :members:

.. automodule:: dogpile.cache.backends.file
    :members:

.. automodule:: dogpile.cache.proxy
    :members:

.. automodule:: dogpile.cache.backends.null
    :members:

Plugins
========

.. automodule:: dogpile.cache.plugins.mako_cache
    :members:

Utilities
=========

.. currentmodule:: dogpile.cache.util

.. autofunction:: function_key_generator

.. autofunction:: sha1_mangle_key

.. autofunction:: length_conditional_mangler

dogpile Core
============

.. autoclass:: dogpile.Lock
    :members:

.. autoclass:: dogpile.NeedRegenerationException
    :members:

.. autoclass:: dogpile.util.ReadWriteMutex
    :members:

.. autoclass:: dogpile.util.NameRegistry
    :members:

