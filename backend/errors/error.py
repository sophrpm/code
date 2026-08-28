
class Error:

    def __init__(self, error_type, description, line, column, fragment=None):
        self.error_type = error_type
        self.description = description
        self.line = line
        self.column = column
        self.fragment = fragment

    #error a diccionario
    def to_dict(self):
        return {
            "type": self.error_type,
            "description": self.description,
            "line": self.line,
            "column": self.column,
            "fragment": self.fragment
        }

    #error a texto
    def __str__(self):
        position = f"Linea {self.line}, Columna {self.column}"
        return f"[{self.error_type}] {self.description} - {position}"