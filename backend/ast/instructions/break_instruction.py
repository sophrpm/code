from ..node import Node
from ...interpreter.result import Result


class BreakInstruction(Node):

    def __init__(self, label, line, column):
        super().__init__(line, column)
        self.label = label

    # Ejecuta break
    def execute(self, environment):
        if not self.inside_loop(environment):
            environment.semantic_error("Sentencia break fuera de un ciclo", self.line, self.column)
            return Result.normal()

        if self.label is not None and not self.label_exists(environment):
            environment.semantic_error(f"No existe un ciclo con la etiqueta '{self.label}'", self.line, self.column)
            return Result.normal()

        return Result.break_result(self.label)

    # Verifica si esta dentro de ciclo
    def inside_loop(self, environment):
        current = environment
        while current is not None:
            if current.name == "main" or current.name.startswith("function:"):
                return False
            if current.name == "loop" or current.name == "while":
                return True
            if current.name.startswith("loop:") or current.name.startswith("while:"):
                return True
            current = current.parent
        return False

    # Verifica etiqueta
    def label_exists(self, environment):
        current = environment
        while current is not None:
            if current.name == "main" or current.name.startswith("function:"):
                return False
            if current.name == "loop:" + self.label or current.name == "while:" + self.label:
                return True
            current = current.parent
        return False
