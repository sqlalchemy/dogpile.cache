from unittest import TestCase

from dogpile.cache import util


class MakoTest(TestCase):
    """ Test entry point for Mako
    """

    def test_entry_point(self):
        import pkg_resources
        
        for impl in pkg_resources.iter_entry_points("mako.cache", "dogpile.cache"):
            print impl
            impl.load()
            return
        else:
            assert 0, "Missing entry point 'dogpile.cache' for 'mako.cache'"
