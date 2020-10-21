===
API
===


Region
======

.. automodule:: dogpile.cache.region
    :members:
    :show-inheritance:

Backend API
=============

See the section :ref:`creating_backends` for details on how to
register new backends or :ref:`changing_backend_behavior` for details on
how to alter the behavior of existing backends.

.. automodule:: dogpile.cache.api
    :members:
    :show-inheritance:


Backends
==========

.. automodule:: dogpile.cache.backends.memory
    :members:
    :show-inheritance:

.. automodule:: dogpile.cache.backends.memcached
    :members:
    :show-inheritance:

.. automodule:: dogpile.cache.backends.redis
    :members:
    :show-inheritance:

.. automodule:: dogpile.cache.backends.file
    :members:
    :show-inheritance:

.. automodule:: dogpile.cache.proxy
    :members:
    :show-inheritance:

.. automodule:: dogpile.cache.backends.null
    :members:
    :show-inheritance:

Exceptions
==========

.. automodule:: dogpile.cache.exception
    :members:
    :show-inheritance:

Plugins
========

.. automodule:: dogpile.cache.plugins.mako_cache
    :members:
    :show-inheritance:

Utilities
=========

.. currentmodule:: dogpile.cache.util

.. autofunction:: function_key_generator

.. autofunction:: kwarg_function_key_generator

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

