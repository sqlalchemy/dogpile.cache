import sys


py3k = sys.version_info >= (3, 0)
jython = sys.platform.startswith('java')


try:
    import threading
except ImportError:
    import dummy_threading as threading


if py3k: # pragma: no cover
    string_types = str,
    text_type = str

    import configparser
    import io
else:
    string_types = basestring,
    text_type = unicode

    import ConfigParser as configparser
    import StringIO as io

if py3k or jython:
    import pickle
else:
    import cPickle as pickle