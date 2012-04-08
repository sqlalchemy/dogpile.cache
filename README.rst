dogpile.cache
=============

Provides a simple caching pattern to use with the `dogpile <http://pypi.python.org/pypi/dogpile>`_
locking system, including rudimentary backends. It effectively completes the
replacement of Beaker as far as caching is concerned, providing an open-ended
and simple pattern to configure caching. New backends are very easy to create
and use; users are encouraged to adapt the provided backends for their own
needs, as high volume caching requires lots of tweaks and adjustments specific
to an application and its environment.

