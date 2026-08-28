#error handling
import math


def sqrt_function(value):

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if not isinstance(value, int) and not isinstance(value, float):
        return None

    if value < 0:
        return None

    return math.sqrt(value)