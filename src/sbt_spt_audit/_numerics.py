"""Finite signed accumulation shared by the audit ledgers."""
from fractions import Fraction
from math import fsum, isfinite


def finite_signed_sum(values, *, context="signed accounting"):
    """Accumulate a finite signed sum; recover intermediate overflow."""
    numbers = [float(value) for value in values]
    if any(not isfinite(value) for value in numbers):
        raise ValueError(f"{context} requires finite signed inputs.")
    try:
        result = fsum(numbers)
    except OverflowError:
        exact = sum((Fraction(value) for value in numbers), Fraction(0))
        try:
            result = float(exact)
        except OverflowError as exc:
            raise ValueError(f"{context} is not representable as a finite binary64 output.") from exc
    if not isfinite(result):
        raise ValueError(f"{context} is not representable as a finite binary64 output.")
    return result
