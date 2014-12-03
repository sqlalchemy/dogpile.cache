import inspect
import pytest
from _pytest.unittest import is_unittest, UnitTestCase

def pytest_pycollect_makeitem(collector, name, obj):
    if is_unittest(obj) and not obj.__name__.startswith("_"):
        return UnitTestCase(name, parent=collector)
    else:
        return []


