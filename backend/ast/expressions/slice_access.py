from ..node import Node
from .identifier import Identifier

from ...interpreter.types import Types


class SliceAccess(Node):

    def __init__(self, array, start, end, line, column):
        super().__init__(line, column)

        self.array = array
        self.start = start
        self.end = end


    # Evalua acceso a slice
    def evaluate(self, environment):

        array_type = self.array.get_type(environment)
        start_type = self.start.get_type(environment)
        end_type = self.end.get_type(environment)

        if array_type != Types.ARRAY:
            self.report_array_error(environment, array_type)
            return None

        if start_type != Types.I32:
            self.report_index_type_error(environment, "inicio", start_type)
            return None

        if end_type != Types.I32:
            self.report_index_type_error(environment, "fin", end_type)
            return None

        array_value = self.array.evaluate(environment)
        start_value = self.start.evaluate(environment)
        end_value = self.end.evaluate(environment)

        if array_value is None:
            return None

        if start_value is None or end_value is None:
            return None

        if start_value < 0:
            self.report_range_error(environment, start_value, end_value, len(array_value))
            return None

        if end_value > len(array_value):
            self.report_range_error( environment, start_value, end_value, len(array_value))
            return None

        if start_value > end_value:
            self.report_range_error(environment, start_value, end_value, len(array_value))
            return None

        return {
            "array": array_value,
            "start": start_value,
            "end": end_value
        }


    # Devuelve tipo slice
    def get_type(self, environment):

        array_type = self.array.get_type(environment)
        start_type = self.start.get_type(environment)
        end_type = self.end.get_type(environment)

        if array_type != Types.ARRAY:
            return Types.UNKNOWN

        if start_type != Types.I32:
            return Types.UNKNOWN

        if end_type != Types.I32:
            return Types.UNKNOWN

        return Types.SLICE


    # Devuelve tipo interno
    def get_element_type(self, environment):

        if isinstance(self.array, Identifier):

            symbol = environment.get(self.array.name)

            if symbol is None:
                self.array.report_not_found(environment)
                return None

            if symbol.data_type != Types.ARRAY:
                return None

            return symbol.element_type

        if hasattr(self.array, "get_element_type"):
            return self.array.get_element_type(environment)

        return None


    # Valida acceso
    def validate(self, environment):

        array_type = self.array.get_type(environment)
        start_type = self.start.get_type(environment)
        end_type = self.end.get_type(environment)

        if array_type != Types.ARRAY:
            self.report_array_error(environment, array_type)
            return False

        if start_type != Types.I32:
            self.report_index_type_error(environment, "inicio", start_type)
            return False

        if end_type != Types.I32:
            self.report_index_type_error(environment, "fin", end_type)
            return False

        array_value = self.array.evaluate(environment)
        start_value = self.start.evaluate(environment)
        end_value = self.end.evaluate(environment)

        if array_value is None:
            return False

        if start_value is None or end_value is None:
            return False

        if (start_value < 0 or end_value > len(array_value) or start_value > end_value):
            self.report_range_error(environment, start_value, end_value, len(array_value))

            return False

        return True


    # Reporta acceso sobre valor no arreglo
    def report_array_error(self, environment, array_type):

        description = ("Se intento crear un slice sobre un valor que no es arreglo, " f"se recibio '{array_type}'")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta tipo de indice incorrecto
    def report_index_type_error(self, environment, position, index_type):

        description = (f"El indice de {position} del slice debe ser i32, " f"se recibio '{index_type}'")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta rango invalido
    def report_range_error(self, environment, start, end, size):

        description = (f"Rango de slice [{start}..{end}] invalido " f"para arreglo de tamaño {size}")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Verifica error duplicado
    def error_exists(self, environment, description):

        if environment.error_manager is None:
            return False

        for error in environment.error_manager.get_errors():
            if (error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column):
                return True

        return False