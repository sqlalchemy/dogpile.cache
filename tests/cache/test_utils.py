from unittest import TestCase

from dogpile.cache import util


class UtilsTest(TestCase):
    """ Test the relevant utils functionality.
    """

    def test_coerce_string_conf(self):
        settings = {'expiration_time': '-1'}
        coerced = util.coerce_string_conf(settings)
        self.assertEqual(coerced['expiration_time'], -1)

        settings = {'expiration_time': '+1'}
        coerced = util.coerce_string_conf(settings)
        self.assertEqual(coerced['expiration_time'], 1)
