from .. import eq_
from unittest import TestCase
from nose import SkipTest

try:
    import mako
except ImportError:
    raise SkipTest("this test suite requires mako templates")

from mako.template import Template
from dogpile.cache import make_region
from mako.cache import register_plugin

register_plugin("dogpile.cache", "dogpile.cache.plugins.mako_cache", "MakoPlugin")

class TestMakoPlugin(TestCase):
    def _memory_fixture(self):
        my_regions = {
            "myregion": make_region().configure(
                        "dogpile.cache.memory",
                    ),
        }
        return {
            'cache_impl': 'dogpile.cache',
            'cache_args': {'regions': my_regions}
        }
    def test_basic(self):
        x = [0]
        def nextx():
            x[0] += 1
            return x[0]

        kw = self._memory_fixture()
        t = Template(
            '<%page cached="True" cache_region="myregion"/>${nextx()}',
            **kw
        )

        eq_(t.render(nextx=nextx), "1")
        eq_(t.render(nextx=nextx), "1")
