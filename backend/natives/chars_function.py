def chars_function(value):

    if value is None:
        return None

    if not isinstance(value, str):
        return None

    return list(value)