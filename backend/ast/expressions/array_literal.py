from ..node import Node
from ...interpreter.types import Types


class ArrayLiteral(Node):
    def __init__(self, expressions, line, column, repeat=None):
        super().__init__(line, column)
        self.expressions = expressions
        self.repeat = repeat

    def get_type(self, environment):
        return Types.ARRAY

    def get_element_type(self, environment):
        return self.expressions[0].get_type(environment) if self.expressions else Types.UNKNOWN

    def evaluate(self, environment):
        values = [expression.evaluate(environment) for expression in self.expressions]
        return values * self.repeat if self.repeat is not None else values
