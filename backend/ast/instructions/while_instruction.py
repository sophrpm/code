# ast/instructions/while_instruction.py

from ..node import Node
from ...interpreter.types import Types
from ...interpreter.result import Result


class WhileInstruction(Node):

    def __init__(self, condition, instructions, line, column, label=None):
        super().__init__(line, column)
        self.condition = condition
        self.instructions = instructions
        self.label = label

    # Ejecuta while
    def execute(self, environment):
        condition_type = self.condition.get_type(environment)
        if condition_type != Types.BOOL:
            self.report_error(environment, f"La condicion de while debe ser bool, se recibio '{condition_type}'")
            return Result.normal()

        while True:
            condition_value = self.condition.evaluate(environment)
            if condition_value is None:
                return Result.normal()
            if condition_value is not True:
                break

            scope_name = "while"
            if self.label is not None:
                scope_name += ":" + self.label

            local_environment = environment.create_child(scope_name)
            result = self.execute_block(local_environment)

            if result.is_return():
                return result

            if result.is_break():
                if result.label is None or result.label == self.label:
                    break
                return result

            if result.is_continue():
                if result.label is None or result.label == self.label:
                    continue
                return result

        return Result.normal()

    # Ejecuta bloque
    def execute_block(self, environment):
        for instruction in self.instructions:
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
