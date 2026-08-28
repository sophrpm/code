# ast/instructions/slice_declaration.py

from ..node import Node
from ...interpreter.symbol import Symbol
from ...interpreter.types import Types
from ...interpreter.result import Result


class SliceDeclaration(Node):

    def __init__(self, name, expression, mutable, line, column):
        super().__init__(line, column)
        self.name = name
        self.expression = expression
        self.mutable = mutable

    # Ejecuta declaracion de slice
    def execute(self, environment):
        if self.expression is None:
            self.report_error(environment, f"El slice '{self.name}' necesita una expresion")
            return Result.normal()

        expression_type = self.expression.get_type(environment)
        if expression_type != Types.SLICE:
            self.report_error(environment, f"La expresion de '{self.name}' debe producir un slice")
            return Result.normal()

        slice_value = self.expression.evaluate(environment)
        if slice_value is None:
            return Result.normal()

        if not Types.is_slice_value(slice_value):
            self.report_error(environment, f"El valor generado para '{self.name}' no es un slice valido")
            return Result.normal()

        element_type = None
        if hasattr(self.expression, "get_element_type"):
            element_type = self.expression.get_element_type(environment)

        if element_type is None:
            self.report_error(environment, f"No se pudo determinar el tipo interno del slice '{self.name}'")
            return Result.normal()

        size = slice_value["end"] - slice_value["start"]
        symbol = Symbol(self.name, slice_value, Types.SLICE, self.mutable, "variable", element_type, size, None, self.line, self.column)

        if not environment.save(symbol, allow_shadowing=True):
            self.report_error(environment, f"No se puede declarar el slice '{self.name}' porque existe un simbolo no reemplazable con ese nombre")

        return Result.normal()

    # Reporta error
    def report_error(self, environment, description):
        if self.error_exists(environment, description):
            return
        environment.semantic_error(description, self.line, self.column)

    # Evita error duplicado
    def error_exists(self, environment, description):
        if environment.error_manager is None:
            return False
        for error in environment.error_manager.get_errors():
            if error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column:
                return True
        return False
