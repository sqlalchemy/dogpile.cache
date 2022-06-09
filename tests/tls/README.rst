=============================
Generate memcached TLS files
=============================

Credit to https://github.com/scoriacorp/docker-tls-memcached

courtesy Moisés Guimarães



Instructions
==============

The certs will expire every two years.

To renew::


    $ cd tests/tls/generate
    $ make clean
    $ make install
    $ git commit -a
    $ git push




