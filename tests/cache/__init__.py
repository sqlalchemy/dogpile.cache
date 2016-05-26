import re
import pytest
from functools import wraps
from dogpile.util import compat
from dogpile.util.compat import configparser, io  # noqa
import time


def eq_(a, b, msg=None):
    """Assert a == b, with repr messaging on failure."""
    assert a == b, msg or "%r != %r" % (a, b)


def is_(a, b, msg=None):
    """Assert a is b, with repr messaging on failure."""
    assert a is b, msg or "%r is not %r" % (a, b)


def ne_(a, b, msg=None):
    """Assert a != b, with repr messaging on failure."""
    assert a != b, msg or "%r == %r" % (a, b)


def assert_raises_message(except_cls, msg, callable_, *args, **kwargs):
    try:
        callable_(*args, **kwargs)
        assert False, "Callable did not raise an exception"
    except except_cls as e:
        assert re.search(msg, str(e)), "%r !~ %s" % (msg, e)


def winsleep():
    # sleep a for an amount of time
    # sufficient for windows time.time()
    # to change
    if compat.win32:
        time.sleep(.001)


def requires_py3k(fn):
    @wraps(fn)
    def wrap(*arg, **kw):
        if compat.py2k:
            pytest.skip("Python 3 required")
        return fn(*arg, **kw)
    return wrap
