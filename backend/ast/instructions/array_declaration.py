from ..node import Node
from ...interpreter.symbol import Symbol
from ...interpreter.types import Types
from ...interpreter.result import Result


class ArrayDeclaration(Node):

    def __init__(self, name, expressions, element_type, size, mutable, line, column, repeat=False):
        super().__init__(line, column)
        self.name = name
        self.expressions = expressions
        self.element_type = element_type
        self.size = size
        self.mutable = mutable
        self.repeat = repeat

    # Ejecuta declaracion de arreglo
    def execute(self, environment):
        if self.expressions is None or len(self.expressions) == 0:
            self.report_error(environment, f"El arreglo '{self.name}' necesita al menos un valor")
            return Result.normal()
        if self.repeat:
            return self.execute_repeat(environment)
        return self.execute_values(environment)

    # Ejecuta arreglo con valores
    def execute_values(self, environment):
        values = []
        final_type = self.element_type

        for expression in self.expressions:
            expression_type = self.get_expression_type(expression, environment)
            if expression_type == Types.UNKNOWN:
                return Result.normal()

            if final_type is None:
                final_type = expression_type

            if not self.types_compatible(final_type, expression_type, expression, environment):
                self.report_error(environment, f"El arreglo '{self.name}' esperaba elementos '{final_type}' y se recibio '{expression_type}'")
                return Result.normal()

            value = expression.evaluate(environment)
            if value is None and expression_type != Types.VOID:
                return Result.normal()

            if final_type == Types.F64 and expression_type == Types.I32:
                value = float(value)

            values.append(value)

        if self.size is not None and len(values) != self.size:
            self.report_error(environment, f"El arreglo '{self.name}' requiere tamaño {self.size} y se recibieron {len(values)} elementos")
            return Result.normal()

        return self.save_array(environment, values, final_type)

    # Ejecuta arreglo por repeticion
    def execute_repeat(self, environment):
        if len(self.expressions) != 1:
            self.report_error(environment, f"El arreglo por repeticion '{self.name}' requiere un solo valor")
            return Result.normal()

        if self.size is None or self.size < 0:
            self.report_error(environment, f"Tamaño invalido para el arreglo '{self.name}'")
            return Result.normal()

        expression = self.expressions[0]
        expression_type = self.get_expression_type(expression, environment)
        if expression_type == Types.UNKNOWN:
            return Result.normal()

        final_type = self.element_type
        if final_type is None:
            final_type = expression_type

        if not self.types_compatible(final_type, expression_type, expression, environment):
            self.report_error(environment, f"El arreglo '{self.name}' esperaba '{final_type}' y se recibio '{expression_type}'")
            return Result.normal()

        value = expression.evaluate(environment)
        if value is None and expression_type != Types.VOID:
            return Result.normal()

        if final_type == Types.F64 and expression_type == Types.I32:
            value = float(value)

        values = []
        for _ in range(self.size):
            values.append(value)

        return self.save_array(environment, values, final_type)

    # Obtiene tipo real
    def get_expression_type(self, expression, environment):
        expression_type = expression.get_type(environment)
        if expression_type == Types.STRUCT and hasattr(expression, "get_struct_name"):
            struct_name = expression.get_struct_name(environment)
            if struct_name is not None:
                return struct_name
        return expression_type

    # Compatibilidad incluyendo structs
    def types_compatible(self, expected_type, received_type, expression, environment):
        if Types.compatible(expected_type, received_type):
            return True
        expected_symbol = environment.get(expected_type)
        if expected_symbol is not None and expected_symbol.kind == "struct":
            if not hasattr(expression, "get_struct_name"):
                return False
            return expression.get_struct_name(environment) == expected_type
        return False

    # Guarda arreglo
    def save_array(self, environment, values, element_type):
        symbol = Symbol(self.name, values, Types.ARRAY, self.mutable, "variable", element_type, len(values), None, self.line, self.column)
        if not environment.save(symbol, allow_shadowing=True):
            self.report_error(environment, f"No se puede declarar el arreglo '{self.name}' porque existe un simbolo no reemplazable con ese nombre")
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
