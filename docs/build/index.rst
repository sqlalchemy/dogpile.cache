==========================================
Welcome to dogpile.cache's documentation!
==========================================

`dogpile.cache <http://bitbucket.org/zzzeek/dogpile.cache>`_ provides a simple
caching pattern based on the `dogpile.core <http://pypi.python.org/pypi/dogpile.core>`_
locking system, including rudimentary backends. It effectively completes the
replacement of `Beaker <http://beaker.groovie.org>`_ as far as caching (though **not** HTTP sessions)
is concerned, providing an open-ended, simple, and higher-performing pattern to configure and use
cache backends. New backends are very easy to create
and use; users are encouraged to adapt the provided backends for their own
needs, as high volume caching requires lots of tweaks and adjustments specific
to an application and its environment.



.. toctree::
   :maxdepth: 2

   front
   usage
   api
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

