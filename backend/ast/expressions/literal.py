from ..node import Node
from ...interpreter.types import Types


class Literal(Node):

    def __init__(self, value, data_type, line, column):
        super().__init__(line, column)
        self.value = value
        self.data_type = data_type

    # Devuelve valor
    def evaluate(self, environment):
        return self.value

    # Devuelve tipo
    def get_type(self, environment=None):
        return self.data_type

    # Convierte valor a texto
    def to_string(self):
        if self.data_type == Types.BOOL:
            if self.value:
                return "true"
            return "false"
        return str(self.value)

    #valor con su tipo
    def validate(self):
        if self.data_type == Types.I32:
            return isinstance(self.value, int) and not isinstance(self.value, bool)
        if self.data_type == Types.F64:
            return isinstance(self.value, float)
        if self.data_type == Types.BOOL:
            return isinstance(self.value, bool)
        if self.data_type == Types.CHAR:
            return isinstance(self.value, str) and len(self.value) == 1
        if self.data_type == Types.STRING:
            return isinstance(self.value, str)
        return False

    # Ejecuta literal como expresion
    def execute(self, environment):
        return self.evaluate(environment)
