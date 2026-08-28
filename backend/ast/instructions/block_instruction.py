from ..node import Node
from ...interpreter.result import Result


class BlockInstruction(Node):

    def __init__(self, instructions, line, column):
        super().__init__(line, column)
        self.instructions = instructions

    # Ejecuta bloque con nuevo scope
    def execute(self, environment):
        block_environment = environment.create_child("block")

        for instruction in self.instructions:
            result = instruction.execute(block_environment)
            if result is None:
                continue
            if not result.is_normal():
                return result

        return Result.normal()
