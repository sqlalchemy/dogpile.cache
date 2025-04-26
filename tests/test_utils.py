from dogpile import util
from dogpile.testing import eq_


class UtilsTest:
    """Test the relevant utils functionality."""

    def test_coerce_string_conf(self):
        settings = {"expiration_time": "-1"}
        coerced = util.coerce_string_conf(settings)
        eq_(coerced["expiration_time"], -1)

        settings = {"expiration_time": "+1"}
        coerced = util.coerce_string_conf(settings)
        eq_(coerced["expiration_time"], 1)
        eq_(type(coerced["expiration_time"]), int)

        settings = {"arguments.lock_sleep": "0.1"}
        coerced = util.coerce_string_conf(settings)
        eq_(coerced["arguments.lock_sleep"], 0.1)

        settings = {"arguments.lock_sleep": "-3.14e-10"}
        coerced = util.coerce_string_conf(settings)
        eq_(coerced["arguments.lock_sleep"], -3.14e-10)
