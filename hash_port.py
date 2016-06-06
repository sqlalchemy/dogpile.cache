"""Helper script which provides an integer
number from a given range based on a hash of 
current directory name.   

This is used in continuous integration as a helper
to provide ports to assign to services like 
Redis, Memcached when they are run on a per-test basis.

E.g. in a Jenkins job, one could put as the run command::

    export TOX_DOGPILE_PORT=`python hash_port.py 10000 34000`
    tox -r -e ${pyv}-${backend}

So you'd get one TOX_DOGPILE_PORT for the script in 
/var/lib/jenkins-workspace/py27-redis, another TOX_DOGPILE_PORT 
for the script in /var/lib/jenkins-workspace/py34-memcached.
tox calls the pifpaf tool to run redis/ memcached local to that
build and has it listen on this port.


"""
import os
import sys

start, end = int(sys.argv[1]), int(sys.argv[2])

dir_ = os.getcwd()

print (hash(dir_) % (end - start)) + start

