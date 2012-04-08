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
register new backends.

.. automodule:: dogpile.cache.api
    :members:

Backends
==========

.. automodule:: dogpile.cache.backends.memory
    :members:

.. automodule:: dogpile.cache.backends.memcached
    :members:

.. automodule:: dogpile.cache.backends.file
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

