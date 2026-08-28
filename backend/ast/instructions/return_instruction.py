# ast/instructions/return_instruction.py

from ..node import Node
from ...interpreter.result import Result
from ...interpreter.types import Types


class ReturnInstruction(Node):

    def __init__(self, expression, line, column):
        super().__init__(line, column)
        self.expression = expression

    # Ejecuta return
    def execute(self, environment):
        if not self.inside_function(environment):
            environment.semantic_error("Sentencia return fuera de una funcion", self.line, self.column)
            return Result.normal()

        if self.expression is None:
            return Result.return_value()

        expression_type = self.expression.get_type(environment)
        if expression_type == Types.UNKNOWN:
            return Result.normal()

        value = self.expression.evaluate(environment)
        if value is None and expression_type != Types.VOID:
            return Result.normal()

        return Result.return_value(value)

    # Verifica si esta dentro de funcion
    def inside_function(self, environment):
        current = environment
        while current is not None:
            if current.name == "main" or current.name.startswith("function:"):
                return True
            current = current.parent
        return False
