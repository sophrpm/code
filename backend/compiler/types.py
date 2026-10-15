#los tipos de arreglo conservan elemento y longitud en una tupla
SCALARS = ('i32', 'f64', 'bool', 'char', 'String', 'void')


def from_info(info):
    if not isinstance(info, dict):
        return info or 'unknown'
    if info['data_type'] == 'array':
        return ('array', from_info(info.get('nested_type', info.get('element_type'))), info['size'])
    return info['data_type']


def array_type(value):
    return isinstance(value, tuple) and value[0] in ('array', 'slice')


def compatible(expected, actual):
    if expected == actual or expected == 'f64' and actual == 'i32':
        return True
    if array_type(expected) and array_type(actual):
        return expected[0] == actual[0] and expected[1] == actual[1] and (expected[2] is None or expected[2] == actual[2])
    return False


def name(value):
    if array_type(value):
        return f'[{name(value[1])}; {value[2]}]' if value[0] == 'array' else f'&[{name(value[1])}]'
    return str(value)


def width(value):
    return width(value[1]) * value[2] if array_type(value) and value[2] is not None else 8
