from ..node import Node
from ...interpreter.symbol import Symbol
from ...interpreter.types import Types
from ...interpreter.result import Result


class Declaration(Node):

    def __init__(self, name, expression, data_type, mutable, line, column):
        super().__init__(line, column)
        self.name = name
        self.expression = expression
        self.data_type = data_type
        self.mutable = mutable

    # Ejecuta declaracion
    def execute(self, environment):
        value = None
        value_type = Types.UNKNOWN
        final_type = self.data_type
        struct_name = None

        if self.expression is not None:
            value_type = self.expression.get_type(environment)
            if value_type == Types.UNKNOWN:
                return Result.normal()

            if value_type == Types.STRUCT and hasattr(self.expression, "get_struct_name"):
                struct_name = self.expression.get_struct_name(environment)

            if final_type is None:
                if struct_name is not None:
                    final_type = struct_name
                else:
                    final_type = value_type

            if not self.types_compatible(final_type, value_type, struct_name, environment):
                self.report_error(environment, f"Tipo incompatible en declaracion de '{self.name}': se esperaba '{final_type}' y se recibio '{value_type}'")
                return Result.normal()

            value = self.expression.evaluate(environment)
            if value is None and value_type != Types.VOID:
                return Result.normal()

            if final_type == Types.F64 and value_type == Types.I32 and value is not None:
                value = float(value)

        else:
            if final_type is None:
                self.report_error(environment, f"La variable '{self.name}' necesita un tipo o un valor inicial")
                return Result.normal()

            value = self.default_value(final_type, environment)
            if value is None and final_type != Types.VOID:
                return Result.normal()

        if struct_name is None:
            struct_symbol = environment.get(final_type)
            if struct_symbol is not None and struct_symbol.kind == "struct":
                struct_name = final_type

        symbol = Symbol(self.name, value, final_type, self.mutable, "variable", None, None, struct_name, self.line, self.column)

        if not environment.save(symbol, allow_shadowing=True):
            self.report_error(environment, f"No se puede declarar '{self.name}' porque existe un simbolo no reemplazable con ese nombre")

        return Result.normal()

    # Valor por defecto
    def default_value(self, data_type, environment):
        if data_type == Types.I32:
            return 0
        if data_type == Types.F64:
            return 0.0
        if data_type == Types.BOOL:
            return False
        if data_type == Types.CHAR:
            return "\0"
        if data_type == Types.STRING:
            return ""

        struct_symbol = environment.get(data_type)
        if struct_symbol is not None and struct_symbol.kind == "struct":
            self.report_error(environment, f"Una variable de tipo struct '{data_type}' debe inicializarse")
            return None

        self.report_error(environment, f"Tipo '{data_type}' no reconocido para la variable '{self.name}'")
        return None

    # Valida compatibilidad
    def types_compatible(self, expected_type, received_type, struct_name, environment):
        if Types.compatible(expected_type, received_type):
            return True

        expected_symbol = environment.get(expected_type)
        if expected_symbol is not None and expected_symbol.kind == "struct":
            return received_type == Types.STRUCT and expected_type == struct_name

        return False

    # Reporta error
    def report_error(self, environment, description):
        if self.error_exists(environment, description):
            return
        environment.semantic_error(description, self.line, self.column)

    # Evita errores duplicados
    def error_exists(self, environment, description):
        if environment.error_manager is None:
            return False
        for error in environment.error_manager.get_errors():
            if error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column:
                return True
        return False
