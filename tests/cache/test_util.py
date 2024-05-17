from dogpile.cache import util


class A:
    @classmethod
    def class_method(cls):
        pass

    @staticmethod
    def static_method():
        pass

    def instance_method(self):
        pass


def test_function_key_generator():
    key_generator = util.function_key_generator(None, A.class_method)
    assert key_generator() == "tests.cache.test_util:A.class_method|"

    key_generator = util.function_key_generator(None, A.static_method)
    assert key_generator() == "tests.cache.test_util:A.static_method|"

    key_generator = util.function_key_generator(None, A.instance_method)
    assert key_generator() == "tests.cache.test_util:A.instance_method|"

    key_generator = util.function_key_generator("namespace", A.class_method)
    assert key_generator() == "tests.cache.test_util:A.class_method|namespace|"
