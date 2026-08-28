from ..node import Node

from ...interpreter.symbol import Symbol
from ...interpreter.types import Types
from ...interpreter.result import Result


class StructDeclaration(Node):

    def __init__(self, name, fields, line, column):
        super().__init__(line, column)

        self.name = name
        self.fields = fields


    # Ejecuta declaracion de struct
    def execute(self, environment):

        # Valida nombre duplicado
        if environment.exists_local(self.name):
            self.report_error(environment, f"El simbolo '{self.name}' ya fue declarado")

            return Result.normal()

        fields_info = {}

        for field in self.fields:
            field_name = field["name"]
            field_type = field["data_type"]

            # Valida campo repetido
            if field_name in fields_info:
                self.report_error(environment, f"El campo '{field_name}' esta repetido en el struct '{self.name}'")

                return Result.normal()


            # Valida tipo
            if not self.valid_field_type(field_type, environment):
                self.report_error(environment, f"Tipo '{field_type}' no valido para el campo '{field_name}' del struct '{self.name}'")

                return Result.normal()

            fields_info[field_name] = field_type

        symbol = Symbol(self.name, fields_info, Types.STRUCT, False, "struct", None, None, None, self.line, self.column)

        if not environment.save(symbol):
            self.report_error(environment, f"No se pudo guardar el struct '{self.name}'")

        return Result.normal()


    # Valida tipo de campo
    def valid_field_type(self, field_type, environment):

        valid_types = (Types.I32, Types.F64, Types.BOOL, Types.CHAR, Types.STRING, Types.ARRAY, Types.SLICE)

        # Tipo normal
        if field_type in valid_types:
            return True

        # Valida nombre de struct
        if not isinstance(field_type, str):
            return False

        if len(field_type) == 0:
            return False

        struct_symbol = environment.get(field_type)

        if struct_symbol is None:
            return False

        return struct_symbol.kind == "struct"


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
            if (error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column):
                return True

        return False