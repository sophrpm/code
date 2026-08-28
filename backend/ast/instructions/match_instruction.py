# ast/instructions/match_instruction.py

from ..node import Node
from ...interpreter.types import Types
from ...interpreter.result import Result


class MatchInstruction(Node):

    def __init__(self, expression, arms, line, column):
        super().__init__(line, column)
        self.expression = expression
        self.arms = arms

    # Ejecuta match
    def execute(self, environment):
        expression_type = self.expression.get_type(environment)
        if expression_type == Types.UNKNOWN:
            return Result.normal()

        expression_value = self.expression.evaluate(environment)
        if expression_value is None and expression_type != Types.VOID:
            return Result.normal()

        default_arm = None
        default_count = 0

        # Valida todos los brazos antes de seleccionar uno
        for index in range(len(self.arms)):
            arm = self.arms[index]
            if arm["default"]:
                default_count += 1
                default_arm = arm
                if index != len(self.arms) - 1:
                    self.report_error(environment, "El caso comodin _ debe ser el ultimo caso del match")
                continue

            pattern_type = arm["pattern"].get_type(environment)
            if not self.compatible_types(expression_type, pattern_type):
                self.report_error(environment, f"Patron de match incompatible: se esperaba '{expression_type}' y se recibio '{pattern_type}'")

        if default_count > 1:
            self.report_error(environment, "La sentencia match solo puede tener un caso comodin")
            return Result.normal()

        for arm in self.arms:
            if arm["default"]:
                continue

            pattern = arm["pattern"]
            pattern_type = pattern.get_type(environment)

            if not self.compatible_types(expression_type, pattern_type):
                continue

            pattern_value = pattern.evaluate(environment)
            if expression_value == pattern_value:
                local_environment = environment.create_child("match")
                result = arm["instruction"].execute(local_environment)
                if result is None:
                    return Result.normal()
                return result

        if default_arm is not None:
            local_environment = environment.create_child("match")
            result = default_arm["instruction"].execute(local_environment)
            if result is None:
                return Result.normal()
            return result

        return Result.normal()

    # Valida tipos
    def compatible_types(self, expression_type, pattern_type):
        if expression_type == pattern_type:
            return True
        return Types.is_numeric(expression_type) and Types.is_numeric(pattern_type)

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
