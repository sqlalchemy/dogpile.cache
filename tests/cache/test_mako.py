from unittest import TestCase


class MakoTest(TestCase):

    """Test entry point for Mako"""

    def test_entry_point(self):
        from importlib import metadata as importlib_metadata

        ep = importlib_metadata.entry_points()
        mako_cache = ep.select(group="mako.cache")
        if mako_cache:
            for impl in mako_cache:
                if impl.name == "dogpile.cache":
                    impl.load()
