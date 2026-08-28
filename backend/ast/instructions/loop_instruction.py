from ..node import Node
from ...interpreter.result import Result


class LoopInstruction(Node):

    def __init__(self, instructions, line, column, label=None):
        super().__init__(line, column)
        self.instructions = instructions
        self.label = label

    # Ejecuta loop
    def execute(self, environment):
        while True:
            scope_name = "loop"
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
