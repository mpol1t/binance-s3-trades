from hypothesis import given
from hypothesis.strategies import booleans


@given(booleans())
def test_double_negation(x):
    assert not not x == x
