# test_target_math_utils.py

def is_even(n: int) -> bool:
    return n % 2 == 0

def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    for i in range(2, int(n**0.5)+1):
        if n % i == 0:
            return False
    return True