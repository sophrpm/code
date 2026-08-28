def abs_function(value):

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int) or isinstance(value, float):
        return abs(value)

    return None