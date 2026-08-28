from ..node import Node
from ...interpreter.symbol import Symbol
from ...interpreter.types import Types
from ...interpreter.result import Result


class MainFunction(Node):

    def __init__(self, instructions, line, column):
        super().__init__(line, column)
        self.instructions = instructions

    # Ejecuta main
    def execute(self, environment):
        if environment.exists_local("main"):
            self.report_error(environment, "El nombre 'main' ya esta utilizado")
            return Result.normal()

        symbol = Symbol("main", self, Types.VOID, False, "function", None, None, None, self.line, self.column)

        if not environment.save(symbol):
            self.report_error(environment, "No se pudo registrar la funcion main")
            return Result.normal()

        main_environment = environment.create_child("main")
        result = self.execute_block(main_environment)

        if result.is_break():
            self.report_error(environment, "Sentencia break fuera de un ciclo")
            return Result.normal()

        if result.is_continue():
            self.report_error(environment, "Sentencia continue fuera de un ciclo")
            return Result.normal()

        if result.is_return():
            if result.value is not None:
                self.report_error(environment, "La funcion main no puede retornar un valor")
            return Result.normal()

        return result

    # Ejecuta instrucciones
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
