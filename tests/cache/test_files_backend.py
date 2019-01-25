from ._fixtures import _GenericBackendTest, _GenericMutexTest
from . import assert_raises_message
import os
import sys

try:
    import fcntl  # noqa
    has_fcntl = True
except ImportError:
    has_fcntl = False


test_basedir = "test_%s.db" % sys.hexversion

if has_fcntl:
    class FilesBackendTest(_GenericBackendTest):
        backend = "dogpile.cache.files"

        config_args = {
            "arguments": {
                "base_dir": test_basedir,
            }
        }


class _FilesMutexTest(_GenericMutexTest):
    backend = "dogpile.cache.files"

    def test_release_assertion_thread(self):
        backend = self._backend()
        m1 = backend.get_mutex("foo")
        assert_raises_message(
            AssertionError,
            "this thread didn't do the acquire",
            m1.release
        )

    def test_release_assertion_key(self):
        backend = self._backend()
        m1 = backend.get_mutex("foo")
        m2 = backend.get_mutex("bar")

        m1.acquire()
        try:
            assert_raises_message(
                AssertionError,
                "No acquire held for key 'bar'",
                m2.release
            )
        finally:
            m1.release()

if has_fcntl:
    class FilesMutexFileTest(_FilesMutexTest):
        config_args = {
            "arguments": {
                "base_dir": test_basedir,
                'distributed_lock': True,
            }
        }


def teardown():
    for fname in os.listdir(os.curdir):
        if fname.startswith(test_basedir):
            os.rmdir(fname)
