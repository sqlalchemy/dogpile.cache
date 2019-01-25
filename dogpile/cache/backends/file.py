"""
File Backends
------------------

Provides backends that deal with local filesystem access.

"""

from __future__ import with_statement

import codecs
import datetime
import errno
import hashlib
import io
import logging
import os
import pickle
import sys
import tempfile
from contextlib import contextmanager
from shutil import copyfileobj

import pytz
import six

from ..api import CacheBackend, NO_VALUE, CachedValue
from ... import util
from ...util import compat

__all__ = 'DBMBackend', 'FilesBackend', 'FileLock', 'AbstractFileLock', 'RangedFileLock'

logger = logging.getLogger(__name__)


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
    for locking; this is **only available on Unix
    platforms**.   An alternative lock implementation, such as one
    which is based on threads or uses a third-party system
    such as `portalocker <https://pypi.python.org/pypi/portalocker>`_,
    can be dropped in using the ``lock_factory`` argument
    in conjunction with the :class:`.AbstractFileLock` base class.

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
    :param lock_factory: a function or class which provides
     for a read/write lock.  Defaults to :class:`.FileLock`.
     Custom implementations need to implement context-manager
     based ``read()`` and ``write()`` functions - the
     :class:`.AbstractFileLock` class is provided as a base class
     which provides these methods based on individual read/write lock
     functions.  E.g. to replace the lock with the dogpile.core
     :class:`.ReadWriteMutex`::

        from dogpile.core.readwrite_lock import ReadWriteMutex
        from dogpile.cache.backends.file import AbstractFileLock

        class MutexLock(AbstractFileLock):
            def __init__(self, filename):
                self.mutex = ReadWriteMutex()

            def acquire_read_lock(self, wait):
                ret = self.mutex.acquire_read_lock(wait)
                return wait or ret

            def acquire_write_lock(self, wait):
                ret = self.mutex.acquire_write_lock(wait)
                return wait or ret

            def release_read_lock(self):
                return self.mutex.release_read_lock()

            def release_write_lock(self):
                return self.mutex.release_write_lock()

        from dogpile.cache import make_region

        region = make_region().configure(
            "dogpile.cache.dbm",
            expiration_time=300,
            arguments={
                "filename": "file.dbm",
                "lock_factory": MutexLock
            }
        )

     While the included :class:`.FileLock` uses ``os.flock()``, a
     windows-compatible implementation can be built using a library
     such as `portalocker <https://pypi.python.org/pypi/portalocker>`_.

     .. versionadded:: 0.5.2



    """

    def __init__(self, arguments):
        self.filename = os.path.abspath(
            os.path.normpath(arguments['filename'])
        )
        dir_, filename = os.path.split(self.filename)

        self.lock_factory = arguments.get("lock_factory", FileLock)
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
            lock = self.lock_factory(os.path.join(basedir, basefile + suffix))
        elif argument is not False:
            lock = self.lock_factory(
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
            dbm = self.dbmmodule.open(
                self.filename,
                "w" if write else "r")
            yield dbm
            dbm.close()

    def get(self, key):
        with self._dbm_file(False) as dbm:
            if hasattr(dbm, 'get'):
                value = dbm.get(key, NO_VALUE)
            else:
                # gdbm objects lack a .get method
                try:
                    value = dbm[key]
                except KeyError:
                    value = NO_VALUE
            if value is not NO_VALUE:
                value = compat.pickle.loads(value)
            return value

    def get_multi(self, keys):
        return [self.get(key) for key in keys]

    def set(self, key, value):
        with self._dbm_file(True) as dbm:
            dbm[key] = compat.pickle.dumps(value,
                                           compat.pickle.HIGHEST_PROTOCOL)

    def set_multi(self, mapping):
        with self._dbm_file(True) as dbm:
            for key, value in mapping.items():
                dbm[key] = compat.pickle.dumps(value,
                                               compat.pickle.HIGHEST_PROTOCOL)

    def delete(self, key):
        with self._dbm_file(True) as dbm:
            try:
                del dbm[key]
            except KeyError:
                pass

    def delete_multi(self, keys):
        with self._dbm_file(True) as dbm:
            for key in keys:
                try:
                    del dbm[key]
                except KeyError:
                    pass


class AbstractFileLock(object):
    """Coordinate read/write access to a file.

    typically is a file-based lock but doesn't necessarily have to be.

    The default implementation here is :class:`.FileLock`.

    Implementations should provide the following methods::

        * __init__()
        * acquire_read_lock()
        * acquire_write_lock()
        * release_read_lock()
        * release_write_lock()

    The ``__init__()`` method accepts a single argument "filename", which
    may be used as the "lock file", for those implementations that use a lock
    file.

    Note that multithreaded environments must provide a thread-safe
    version of this lock.  The recommended approach for file-
    descriptor-based locks is to use a Python ``threading.local()`` so
    that a unique file descriptor is held per thread.  See the source
    code of :class:`.FileLock` for an implementation example.


    """

    def __init__(self, filename):
        """Constructor, is given the filename of a potential lockfile.

        The usage of this filename is optional and no file is
        created by default.

        Raises ``NotImplementedError`` by default, must be
        implemented by subclasses.
        """
        raise NotImplementedError()

    def acquire(self, wait=True):
        """Acquire the "write" lock.

        This is a direct call to :meth:`.AbstractFileLock.acquire_write_lock`.

        """
        return self.acquire_write_lock(wait)

    def release(self):
        """Release the "write" lock.

        This is a direct call to :meth:`.AbstractFileLock.release_write_lock`.

        """
        self.release_write_lock()

    @contextmanager
    def read(self):
        """Provide a context manager for the "read" lock.

        This method makes use of :meth:`.AbstractFileLock.acquire_read_lock`
        and :meth:`.AbstractFileLock.release_read_lock`

        """

        self.acquire_read_lock(True)
        try:
            yield
        finally:
            self.release_read_lock()

    @contextmanager
    def write(self):
        """Provide a context manager for the "write" lock.

        This method makes use of :meth:`.AbstractFileLock.acquire_write_lock`
        and :meth:`.AbstractFileLock.release_write_lock`

        """

        self.acquire_write_lock(True)
        try:
            yield
        finally:
            self.release_write_lock()

    @property
    def is_open(self):
        """optional method."""
        raise NotImplementedError()

    def acquire_read_lock(self, wait):
        """Acquire a 'reader' lock.

        Raises ``NotImplementedError`` by default, must be
        implemented by subclasses.
        """
        raise NotImplementedError()

    def acquire_write_lock(self, wait):
        """Acquire a 'write' lock.

        Raises ``NotImplementedError`` by default, must be
        implemented by subclasses.
        """
        raise NotImplementedError()

    def release_read_lock(self):
        """Release a 'reader' lock.

        Raises ``NotImplementedError`` by default, must be
        implemented by subclasses.
        """
        raise NotImplementedError()

    def release_write_lock(self):
        """Release a 'writer' lock.

        Raises ``NotImplementedError`` by default, must be
        implemented by subclasses.
        """
        raise NotImplementedError()


class FileLock(AbstractFileLock):
    """Use lockfiles to coordinate read/write access to a file.

    Only works on Unix systems, using
    `fcntl.flock() <http://docs.python.org/library/fcntl.html>`_.

    """

    def __init__(self, filename):
        self._filedescriptor = compat.threading.local()
        self.filename = filename

    @util.memoized_property
    def _module(self):
        import fcntl
        return fcntl

    @property
    def is_open(self):
        return hasattr(self._filedescriptor, 'fileno')

    def acquire_read_lock(self, wait):
        return self._acquire(wait, os.O_RDONLY, self._module.LOCK_SH)

    def acquire_write_lock(self, wait):
        return self._acquire(wait, os.O_WRONLY, self._module.LOCK_EX)

    def release_read_lock(self):
        self._release()

    def release_write_lock(self):
        self._release()

    def _acquire(self, wait, wrflag, lockflag):
        wrflag |= os.O_CREAT
        fileno = os.open(self.filename, wrflag)
        try:
            if not wait:
                lockflag |= self._module.LOCK_NB
            self._module.flock(fileno, lockflag)
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
            self._module.flock(fileno, self._module.LOCK_UN)
            os.close(fileno)
            del self._filedescriptor.fileno


def _remove(file_path):
    try:
        os.remove(file_path)
    except (IOError, OSError):
        logger.exception('Cannot remove file {}'.format(file_path))


def _ensure_dir(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise
    except (OSError, IOError):
        logger.exception('Cannot create directory {}'.format(path))


def _stat(file_path):
    try:
        return os.stat(file_path)
    except (IOError, OSError):
        logger.exception('Cannot stat file {}'.format(file_path))
        return None


def _get_size(stat):
    if stat is None:
        return 0
    return stat.st_size


def _get_last_modified(stat):
    if stat is None:
        return datetime.datetime.fromtimestamp(0, tz=pytz.utc)
    return datetime.datetime.fromtimestamp(stat.st_mtime, pytz.utc)


def without_suffixes(string, suffixes):
    for suffix in suffixes:
        if string.endswith(suffix):
            return string[:-len(suffix)]
    return string


def sha256_mangler(key):
    if isinstance(key, six.text_type):
        key = key.encode('utf-8')
    return hashlib.sha256(key).hexdigest()


class FilesBackend(CacheBackend):
    """A file-backend using files to store keys.

    Basic usage::

        from dogpile.cache import make_region

        region = make_region().configure(
            'paylogic.files_backend',
            expiration_time = datetime.timedelta(seconds=30),
            arguments = {
                "base_dir": "/path/to/cachedir",
                "file_movable": True,
                "cache_size": 1024*1024*1024,  # 1 Gb
                "expiration_time: datetime.timedelta(seconds=30),
            }
        )

        @region.cache_on_arguments()
        def big_file_operation(args):
            f = tempfile.NamedTemporaryFile(delete=False)
            # fill the file
            f.flush()
            f.seek(0)
            return f


    Parameters to the ``arguments`` dictionary are
    below.

    :param base_dir: path of the directory where to store the files.
    :param expiration_time: expiration time of the keys
    :param cache_size: the maximum size of the directory. Once exceeded, keys will be removed in a
                       LRU fashion.
    :param file_movable: whether the file provided to .set() can be moved. If that's the case,
                         the backend will avoid copying the contents.
    """

    @staticmethod
    def key_mangler(key):
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def __init__(self, arguments):
        # TODO: Add self.lock_expiration
        self.base_dir = os.path.abspath(
            os.path.normpath(arguments['base_dir'])
        )
        _ensure_dir(self.base_dir)

        self.values_dir = os.path.join(self.base_dir, 'values')
        _ensure_dir(self.values_dir)

        self.dogpile_lock_path = os.path.join(self.base_dir, 'dogpile.lock')
        self.rw_lock_path = os.path.join(self.base_dir, 'rw.lock')

        self.expiration_time = arguments.get('expiration_time')
        self.cache_size = arguments.get('cache_size', 1024 * 1024 * 1024)  # 1 Gb
        self.file_movable = arguments.get('file_movable', False)
        self.distributed_lock = arguments.get('distributed_lock', True)


    def _get_rw_lock(self, key):
        return RangedFileLock(self.rw_lock_path, key)

    def _get_dogpile_lock(self, key):
        return RangedFileLock(self.dogpile_lock_path, key)

    def get_mutex(self, key):
        if self.distributed_lock:
            return self._get_dogpile_lock(key)

            # # We need to hash the key, as it may not have used our key mangler
            # hash = hashlib.sha256(key.encode('utf-8')).hexdigest()
            # partition_key = hash[:self.dogpile_lock_partition_size * 2]
            # return FileLock(os.path.join(self.base_dir, 'dogpile_locks', partition_key))
        else:
            return None

    def _file_path_payload(self, key):
        return os.path.join(self.values_dir, key + '.payload')

    def _file_path_metadata(self, key):
        return os.path.join(self.values_dir, key + '.metadata')

    def _file_path_type(self, key):
        return os.path.join(self.values_dir, key + '.type')

    def get(self, key):
        now = datetime.datetime.now(tz=pytz.utc)
        file_path_payload = self._file_path_payload(key)
        file_path_metadata = self._file_path_metadata(key)
        file_path_type = self._file_path_type(key)
        with self._get_rw_lock(key).read():
            if not os.path.exists(file_path_payload) or not os.path.exists(file_path_metadata)\
                    or not os.path.exists(file_path_type):
                return NO_VALUE
            if self.expiration_time is not None:
                if _get_last_modified(_stat(file_path_payload)) < now - self.expiration_time:
                    return NO_VALUE

            with open(file_path_metadata, 'rb') as i:
                metadata = pickle.load(i)
            with open(file_path_type, 'rb') as i:
                type = pickle.load(i)
            if type == 'file':
                return CachedValue(
                    open(file_path_payload, 'rb'),
                    metadata,
                )
            elif metadata is not None:
                with open(file_path_payload, 'rb') as i:
                    return CachedValue(
                        pickle.load(i),
                        metadata,
                    )
            else:
                with open(file_path_payload, 'rb') as i:
                    return pickle.load(i)

    def get_multi(self, keys):
        return [self.get(key) for key in keys]

    def set(self, key, value):
        self._prune()
        if isinstance(value, CachedValue):
            payload, metadata = value.payload, value.metadata
        else:
            payload, metadata = value, None
        with tempfile.NamedTemporaryFile(delete=False) as metadata_file:
            pickle.dump(metadata, metadata_file, pickle.HIGHEST_PROTOCOL)

        if not isinstance(payload, io.IOBase):
            type = 'value'
            with tempfile.NamedTemporaryFile(delete=False) as payload_file:
                pickle.dump(payload, payload_file, pickle.HIGHEST_PROTOCOL)
            payload_file_path = payload_file.name
        else:
            type = 'file'
            if self.file_movable and hasattr(payload, 'name'):
                payload_file_path = payload.name
            else:
                payload.seek(0)

                with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
                    copyfileobj(payload, tmpfile, length=1024 * 1024)
                payload_file_path = tmpfile.name

        with tempfile.NamedTemporaryFile(delete=False) as type_file:
            pickle.dump(type, type_file, pickle.HIGHEST_PROTOCOL)

        with self._get_rw_lock(key).write():
            os.rename(metadata_file.name, self._file_path_metadata(key))
            os.rename(type_file.name, self._file_path_type(key))
            os.rename(payload_file_path, self._file_path_payload(key))

    def set_multi(self, mapping):
        for key, value in mapping.items():
            self.set(key, value)

    def delete(self, key):
        with self._get_rw_lock(key).write():
            self._delete_key_files(key)

    def delete_multi(self, keys):
        for key in keys:
            self.delete(key)

    def _delete_key_files(self, key):
        _remove(self._file_path_payload(key))
        _remove(self._file_path_metadata(key))

    def _list_keys_with_desc(self):
        suffixes = ['.payload', '.metadata', '.type']
        files = [
            file_name for file_name in os.listdir(self.values_dir)
            if any(file_name.endswith(s) for s in suffixes)
        ]
        files_with_stats = {
            f: _stat(os.path.join(self.values_dir, f)) for f in files
        }

        keys = set(
            without_suffixes(f, suffixes)
            for f in files
        )

        return {
            key: {
                'last_modified': _get_last_modified(files_with_stats.get(key + '.payload', None)),
                'size': (
                        _get_size(files_with_stats.get(key + '.payload'))
                        + _get_size(files_with_stats.get(key + '.metadata'))
                        + _get_size(files_with_stats.get(key + '.type'))
                ),
            }
            for key in keys
        }

    def attempt_delete_key(self, key):
        rw_lock = self._get_rw_lock(key)
        if rw_lock.acquire_write_lock(wait=False):
            try:
                self._delete_key_files(key)
            finally:
                rw_lock.release_write_lock()

    def _prune(self):
        now = datetime.datetime.now(tz=pytz.utc)
        keys_with_desc = self._list_keys_with_desc()
        keys = set(keys_with_desc)
        remaining_keys = set(keys_with_desc)

        if self.expiration_time is not None:
            for key in keys:
                if keys_with_desc[key]['last_modified'] >= now - self.expiration_time:
                    continue
                self.attempt_delete_key(key)
                remaining_keys.discard(key)

        keys_by_newest = sorted(
            remaining_keys,
            key=lambda key: keys_with_desc[key]['last_modified'],
            reverse=True,
        )
        while sum((keys_with_desc[key]['size'] for key in remaining_keys), 0) > self.cache_size:
            if not keys_by_newest:
                break
            key = keys_by_newest.pop()
            self.attempt_delete_key(key)


def _key_to_offset(key, max=sys.maxint):
    # Map any string to randomly distributed integers between 0 and max
    hash = hashlib.sha1(key.encode('utf-8')).digest()
    return int(codecs.encode(hash, 'hex'), 16) % max


class RangedFileLock(AbstractFileLock):
    def __init__(self, path, key=None):
        if key is None:
            self.key_offset = None
        else:
            self.key_offset = _key_to_offset(key)
        self._filedescriptor = None
        self.path = path

    @util.memoized_property
    def _module(self):
        import fcntl
        return fcntl

    def acquire_read_lock(self, wait):
        return self._acquire(wait, os.O_RDONLY, self._module.LOCK_SH)

    def acquire_write_lock(self, wait):
        return self._acquire(wait, os.O_WRONLY, self._module.LOCK_EX)

    def release_read_lock(self):
        self._release()

    def release_write_lock(self):
        self._release()

    def _acquire(self, wait, wrflag, lockflag):
        wrflag |= os.O_CREAT
        fileno = os.open(self.path, wrflag)
        try:
            if not wait:
                lockflag |= self._module.LOCK_NB
            if self.key_offset is not None:
                self._module.lockf(fileno, lockflag, 1, self.key_offset)
            else:
                self._module.lockf(fileno, lockflag)
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
            self._filedescriptor = fileno
            return True

    def _release(self):
        if self._filedescriptor is None:
            return
        if self.key_offset is not None:
            self._module.lockf(self._filedescriptor, self._module.LOCK_UN, 1, self.key_offset)
        else:
            self._module.lockf(self._filedescriptor, self._module.LOCK_UN)
        os.close(self._filedescriptor)
