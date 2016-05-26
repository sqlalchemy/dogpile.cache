==========================================
Welcome to dogpile.cache's documentation!
==========================================

Dogpile consists of two subsystems, one building on top of the other.

``dogpile`` provides the concept of a "dogpile lock", a control structure
which allows a single thread of execution to be selected as the "creator" of
some resource, while allowing other threads of execution to refer to the previous
version of this resource as the creation proceeds; if there is no previous
version, then those threads block until the object is available.

``dogpile.cache`` is a caching API which provides a generic interface to
caching backends of any variety, and additionally provides API hooks which
integrate these cache backends with the locking mechanism of ``dogpile``.

New backends are very easy to create and use; users are encouraged to adapt the
provided backends for their own needs, as high volume caching requires lots of
tweaks and adjustments specific to an application and its environment.


.. toctree::
   :maxdepth: 2

   front
   usage
   recipes
   core_usage
   api
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

