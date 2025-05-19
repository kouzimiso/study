# test_math_utils.py

from hypothesis import given, strategies as st
import test_target_math_utils

@given(st.integers())
def test_is_even_property(n):
    result = test_target_math_utils.is_even(n)
    print(f"Testing is_even({n}) => {result}")
    assert result == (n % 2 == 0)

@given(st.integers(min_value=0, max_value=100))
def test_is_prime_returns_bool(n):
    result = test_target_math_utils.is_prime(n)
    print(f"Testing is_prime({n}) => {result}")
    assert isinstance(result, bool)