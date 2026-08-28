from ..node import Node
from ...interpreter.types import Types
from ...interpreter.result import Result


class IfInstruction(Node):

    def __init__(self, condition, instructions, else_instructions, line, column):
        super().__init__(line, column)
        self.condition = condition
        self.instructions = instructions
        self.else_instructions = else_instructions

    # Ejecuta if
    def execute(self, environment):
        condition_type = self.condition.get_type(environment)
        if condition_type != Types.BOOL:
            self.report_error(environment, f"La condicion de if debe ser bool, se recibio '{condition_type}'")
            return Result.normal()

        condition_value = self.condition.evaluate(environment)
        if condition_value is None:
            return Result.normal()

        if condition_value is True:
            local_environment = environment.create_child("if")
            return self.execute_block(self.instructions, local_environment)

        if self.else_instructions:
            local_environment = environment.create_child("else")
            return self.execute_block(self.else_instructions, local_environment)

        return Result.normal()

    # Ejecuta bloque
    def execute_block(self, instructions, environment):
        for instruction in instructions:
            result = instruction.execute(environment)
            if result is None:
                continue
            if not result.is_normal():
                return result
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
