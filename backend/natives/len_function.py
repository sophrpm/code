#falta error handlin
def len_function(value):

    if value is None:
        return None

    if isinstance(value, str):
        return len(value)

    if isinstance(value, list):
        return len(value)

    if isinstance(value, dict):
        if "array" in value and "start" in value and "end" in value:
            return value["end"] - value["start"]

    return None