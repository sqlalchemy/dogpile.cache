import sys

py2k = sys.version_info < (3, 0)
py3k = sys.version_info >= (3, 0)
py32 = sys.version_info >= (3, 2)
py38 = sys.version_info >= (3, 8)
py27 = sys.version_info >= (2, 7)
jython = sys.platform.startswith("java")
win32 = sys.platform.startswith("win")

try:
    import threading
except ImportError:
    import dummy_threading as threading  # noqa


if py3k:  # pragma: no cover
    string_types = (str,)
    text_type = str
    string_type = str

    if py32:
        callable = callable  # noqa
    else:

        def callable(fn):  # noqa
            return hasattr(fn, "__call__")

    def u(s):
        return s

    def ue(s):
        return s

    import configparser
    import io
    import _thread as thread
else:
    # Using noqa bellow due to tox -e pep8 who use
    # python3.7 as the default interpreter
    string_types = (basestring,)  # noqa
    text_type = unicode  # noqa
    string_type = str

    def u(s):
        return unicode(s, "utf-8")  # noqa

    def ue(s):
        return unicode(s, "unicode_escape")  # noqa

    import ConfigParser as configparser  # noqa
    import StringIO as io  # noqa

    callable = callable  # noqa
    import thread  # noqa


if py3k:
    import collections

    ArgSpec = collections.namedtuple(
        "ArgSpec", ["args", "varargs", "keywords", "defaults"]
    )

    if py38:
        from inspect import signature

        def inspect_getargspec(func):
            sig = signature(func)
            args = []
            varargs = None
            varkw = None
            kwonlyargs = []
            defaults = ()
            annotations = {}
            defaults = ()
            kwdefaults = {}
            for param in sig.parameters.values():
                kind = param.kind
                name = param.name

                if kind is param.POSITIONAL_ONLY:
                    args.append(name)
                elif kind is param.POSITIONAL_OR_KEYWORD:
                    args.append(name)
                    if param.default is not param.empty:
                        defaults += (param.default,)
                elif kind is param.VAR_POSITIONAL:
                    varargs = name
                elif kind is param.KEYWORD_ONLY:
                    kwonlyargs.append(name)
                    if param.default is not param.empty:
                        kwdefaults[name] = param.default
                elif kind is param.VAR_KEYWORD:
                    varkw = name

                if param.annotation is not param.empty:
                    annotations[name] = param.annotation

            if not kwdefaults:
                # compatibility with 'func.__kwdefaults__'
                kwdefaults = None

            if not defaults:
                # compatibility with 'func.__defaults__'
                defaults = None

            return ArgSpec(args, varargs, varkw, defaults)

    else:
        from inspect import getfullargspec as inspect_getfullargspec

        def inspect_getargspec(func):
            return ArgSpec(*inspect_getfullargspec(func)[0:4])


else:
    from inspect import getargspec as inspect_getargspec  # noqa

if py3k or jython:
    import pickle
else:
    import cPickle as pickle  # noqa

if py3k:

    def read_config_file(config, fileobj):
        return config.read_file(fileobj)


else:

    def read_config_file(config, fileobj):
        return config.readfp(fileobj)


def timedelta_total_seconds(td):
    if py27:
        return td.total_seconds()
    else:
        return (
            td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6
        ) / 1e6
