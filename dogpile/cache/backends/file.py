"""
File Backends
------------------

Provides backends that deal with local filesystem access.

"""

from dogpile.cache.api import CacheBackend, NO_VALUE
from contextlib import contextmanager
from dogpile.cache import compat
from dogpile.cache import util
import os
import fcntl

__all__ = 'DBMBackend', 'FileLock'

class DBMBackend(CacheBackend):
    """A file-backend using a dbm file to store keys.

    Basic usage::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.dbm',
            expiration_time = 3600,
            arguments = {
                "filename":"/path/to/cachefile.dbm"
            }
        )

    DBM access is provided using the Python ``anydbm`` module,
    which selects a platform-specific dbm module to use.
    This may be made to be more configurable in a future
    release.

    Note that different dbm modules have different behaviors.
    Some dbm implementations handle their own locking, while
    others don't.  The :class:`.DBMBackend` uses a read/write
    lockfile by default, which is compatible even with those
    DBM implementations for which this is unnecessary,
    though the behavior can be disabled.

    The DBM backend by default makes use of two lockfiles.
    One is in order to protect the DBM file itself from
    concurrent writes, the other is to coordinate
    value creation (i.e. the dogpile lock).  By default,
    these lockfiles use the ``flock()`` system call
    for locking; this is only available on Unix
    platforms.

    Currently, the dogpile lock is against the entire
    DBM file, not per key.   This means there can
    only be one "creator" job running at a time
    per dbm file.

    A future improvement might be to have the dogpile lock
    using a filename that's based on a modulus of the key.
    Locking on a filename that uniquely corresponds to the
    key is problematic, since it's not generally safe to
    delete lockfiles as the application runs, implying an
    unlimited number of key-based files would need to be
    created and never deleted.

    Parameters to the ``arguments`` dictionary are
    below.

    :param filename: path of the filename in which to
     create the DBM file.  Note that some dbm backends
     will change this name to have additional suffixes.
    :param rw_lockfile: the name of the file to use for
     read/write locking.  If omitted, a default name
     is used by appending the suffix ".rw.lock" to the
     DBM filename.  If False, then no lock is used.
    :param dogpile_lockfile: the name of the file to use
     for value creation, i.e. the dogpile lock.  If
     omitted, a default name is used by appending the
     suffix ".dogpile.lock" to the DBM filename. If
     False, then dogpile.cache uses the default dogpile
     lock, a plain thread-based mutex.


    """
    def __init__(self, arguments):
        self.filename = os.path.abspath(
                            os.path.normpath(arguments['filename'])
                        )
        dir_, filename = os.path.split(self.filename)

        self._rw_lock = self._init_lock(
                                arguments.get('rw_lockfile'),
                                ".rw.lock", dir_, filename)
        self._dogpile_lock = self._init_lock(
                                arguments.get('dogpile_lockfile'),
                                ".dogpile.lock",
                                dir_, filename,
                                util.KeyReentrantMutex.factory)

        # TODO: make this configurable
        if compat.py3k:
            import dbm
        else:
            import anydbm as dbm
        self.dbmmodule = dbm
        self._init_dbm_file()

    def _init_lock(self, argument, suffix, basedir, basefile, wrapper=None):
        if argument is None:
            lock = FileLock(os.path.join(basedir, basefile + suffix))
        elif argument is not False:
            lock = FileLock(
                        os.path.abspath(
                            os.path.normpath(argument)
                        ))
        else:
            return None
        if wrapper:
            lock = wrapper(lock)
        return lock

    def _init_dbm_file(self):
        exists = os.access(self.filename, os.F_OK)
        if not exists:
            for ext in ('db', 'dat', 'pag', 'dir'):
                if os.access(self.filename + os.extsep + ext, os.F_OK):
                    exists = True
                    break
        if not exists:
            fh = self.dbmmodule.open(self.filename, 'c')
            fh.close()

    def get_mutex(self, key):
        # using one dogpile for the whole file.   Other ways
        # to do this might be using a set of files keyed to a
        # hash/modulus of the key.   the issue is it's never
        # really safe to delete a lockfile as this can
        # break other processes trying to get at the file
        # at the same time - so handling unlimited keys
        # can't imply unlimited filenames
        if self._dogpile_lock:
            return self._dogpile_lock(key)
        else:
            return None

    @contextmanager
    def _use_rw_lock(self, write):
        if self._rw_lock is None:
            yield
        elif write:
            with self._rw_lock.write():
                yield
        else:
            with self._rw_lock.read():
                yield

    @contextmanager
    def _dbm_file(self, write):
        with self._use_rw_lock(write):
            dbm = self.dbmmodule.open(self.filename,
                                "w" if write else "r")
            yield dbm
            dbm.close()

    def get(self, key):
        with self._dbm_file(False) as dbm:
            value = dbm.get(key, NO_VALUE)
            if value is not NO_VALUE:
                value = compat.pickle.loads(value)
            return value

    def set(self, key, value):
        with self._dbm_file(True) as dbm:
            dbm[key] = compat.pickle.dumps(value)

    def delete(self, key):
        with self._dbm_file(True) as dbm:
            try:
                del dbm[key]
            except KeyError:
                pass

class FileLock(object):
    """Use lockfiles to coordinate read/write access to a file.

    Only works on Unix systems, using
    `fcntl.flock() <http://docs.python.org/library/fcntl.html>`_.

    """

    def __init__(self, filename):
        self._filedescriptor = compat.threading.local()
        self.filename = filename

    def acquire(self, wait=True):
        return self.acquire_write_lock(wait)

    def release(self):
        self.release_write_lock()

    @property
    def is_open(self):
        return hasattr(self._filedescriptor, 'fileno')

    @contextmanager
    def read(self):
        self.acquire_read_lock(True)
        yield
        self.release_read_lock()

    @contextmanager
    def write(self):
        self.acquire_write_lock(True)
        yield
        self.release_write_lock()

    def acquire_read_lock(self, wait):
        return self._acquire(wait, os.O_RDONLY, fcntl.LOCK_SH)

    def acquire_write_lock(self, wait):
        return self._acquire(wait, os.O_WRONLY, fcntl.LOCK_EX)

    def release_read_lock(self):
        self._release()

    def release_write_lock(self):
        self._release()

    def _acquire(self, wait, wrflag, lockflag):
        wrflag |= os.O_CREAT
        fileno = os.open(self.filename, wrflag)
        try:
            if not wait:
                lockflag |= fcntl.LOCK_NB
            fcntl.flock(fileno, lockflag)
        except IOError:
            os.close(fileno)
            if not wait:
                # this is typically
                # "[Errno 35] Resource temporarily unavailable",
                # because of LOCK_NB
                return False
            else:
                raise
        else:
            self._filedescriptor.fileno = fileno
            return True

    def _release(self):
        try:
            fileno = self._filedescriptor.fileno
        except AttributeError:
            return
        else:
            fcntl.flock(fileno, fcntl.LOCK_UN)
            os.close(fileno)
            del self._filedescriptor.fileno
