#falta error handlin
def string_from(value):

    if value is None:
        return ""

    if isinstance(value, bool):
        if value:
            return "true"

        return "false"

    return str(value)