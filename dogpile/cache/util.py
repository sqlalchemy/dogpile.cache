from hashlib import sha1
import inspect
import sys

try:
    import threading
except ImportError:
    import dummy_threading as threading

py3k = sys.version_info >= (3, 0)
jython = sys.platform.startswith('java')

if py3k or jython:
    import pickle
else:
    import cPickle as pickle

if py3k:
    tounicode = str
else:
    tounicode = unicode

class PluginLoader(object):
    def __init__(self, group):
        self.group = group
        self.impls = {}

    def load(self, name):
        if name in self.impls:
             return self.impls[name]()
        else:
            import pkg_resources
            for impl in pkg_resources.iter_entry_points(
                                self.group, 
                                name):
                self.impls[name] = impl.load
                return impl.load()
            else:
                raise Exception(
                        "Can't load plugin %s %s" % 
                        (self.group, name))

    def register(self, name, modulepath, objname):
        def load():
            mod = __import__(modulepath)
            for token in modulepath.split(".")[1:]:
                mod = getattr(mod, token)
            return getattr(mod, objname)
        self.impls[name] = load


def function_key_generator(namespace, fn):
    """Return a function that generates a string
    key, based on a given function as well as
    arguments to the returned function itself.
    
    This is used by :meth:`.CacheRegion.cache_on_arguments`
    to generate a cache key from a decorated function.
    
    It can be replaced using the ``function_key_generator``
    argument passed to :func:`.make_region`.
    
    """

    if namespace is None:
        namespace = '%s:%s' % (fn.__module__, fn.__name__)
    else:
        namespace = '%s:%s|%s' % (fn.__module__, fn.__name__, namespace)

    args = inspect.getargspec(fn)
    has_self = args[0] and args[0][0] in ('self', 'cls')
    def generate_key(*args, **kw):
        if kw:
            raise ValueError(
                    "dogpile.cache's default key creation "
                    "function does not accept keyword arguments.")
        if has_self:
            args = args[1:]
        return namespace + "|" + " ".join(map(tounicode, args))
    return generate_key

def sha1_mangle_key(key):
    """a SHA1 key mangler."""

    return sha1(key).hexdigest()

def length_conditional_mangler(length, mangler):
    """a key mangler that mangles if the length of the key is
    past a certain threshold.
    
    """
    def mangle(key):
        if len(key) >= length:
            return mangler(key)
        else:
            return key
    return mangle

class memoized_property(object):
    """A read-only @property that is only evaluated once."""
    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result

def to_list(x, default=None):
    """Coerce to a list."""
    if x is None:
        return default
    if not isinstance(x, (list, tuple)):
        return [x]
    else:
        return x
