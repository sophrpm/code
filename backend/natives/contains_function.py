def contains_function(value, search):

    if value is None:
        return None

    if isinstance(value, str):
        return search in value

    if isinstance(value, list):
        return search in value

    if isinstance(value, dict):
        if "array" in value and "start" in value and "end" in value:
            array = value["array"]
            start = value["start"]
            end = value["end"]

            for index in range(start, end):
                if array[index] == search:
                    return True

            return False

    return None