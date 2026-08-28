def array_push(array, value):

    if not isinstance(array, list):
        return None

    array.append(value)

    return array


def array_remove(array, index):

    if not isinstance(array, list):
        return None

    if not isinstance(index, int):
        return None

    if isinstance(index, bool):
        return None

    if index < 0:
        return None

    if index >= len(array):
        return None

    return array.pop(index)