class Symbol:

    def __init__(self, name, value, data_type=None, mutable=False, kind="variable", element_type=None, size=None, struct_name=None, line=None, column=None):

        self.name = name
        self.value = value
        self.data_type = data_type
        self.mutable = mutable
        self.kind = kind

        self.element_type = element_type
        self.size = size
        self.struct_name = struct_name

        self.line = line
        self.column = column