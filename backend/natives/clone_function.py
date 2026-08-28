#falta error handlin
def clone_function(value):

    if value is None:
        return None

    if isinstance(value, list):
        return value.copy()

    if isinstance(value, dict):
        return value.copy()

    if isinstance(value, str):
        return value

    if isinstance(value, bool):
        return value

    if isinstance(value, int) or isinstance(value, float):
        return value

    return None