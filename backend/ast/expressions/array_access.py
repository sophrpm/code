# ast/expressions/array_access.py

from ..node import Node
from .identifier import Identifier

from ...interpreter.types import Types


class ArrayAccess(Node):

    def __init__(self, array, index, line, column):
        super().__init__(line, column)

        self.array = array
        self.index = index


    # Evalua acceso al arreglo
    def evaluate(self, environment):

        array_type = self.array.get_type(environment)
        index_type = self.index.get_type(environment)

        if array_type != Types.ARRAY:
            self.report_array_error(environment, array_type)
            return None

        if index_type != Types.I32:
            self.report_index_type_error(environment, index_type)
            return None

        array_value = self.array.evaluate(environment)
        index_value = self.index.evaluate(environment)

        if array_value is None or index_value is None:
            return None

        if index_value < 0 or index_value >= len(array_value):
            self.report_index_range_error(environment, index_value, len(array_value))
            return None

        return array_value[index_value]


    #tipo del elemento
    def get_type(self, environment):

        array_type = self.array.get_type(environment)

        if array_type != Types.ARRAY:
            return Types.UNKNOWN

        element_type = self.get_element_type(environment)

        if element_type is None:
            return Types.UNKNOWN

        return element_type


    #tipo interno del arreglo
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
        index_type = self.index.get_type(environment)

        if array_type != Types.ARRAY:
            self.report_array_error(environment, array_type)
            return False

        if index_type != Types.I32:
            self.report_index_type_error(environment, index_type)
            return False

        array_value = self.array.evaluate(environment)
        index_value = self.index.evaluate(environment)

        if array_value is None or index_value is None:
            return False

        if index_value < 0 or index_value >= len(array_value):
            self.report_index_range_error(environment, index_value, len(array_value))
            return False

        return True


    #acceso sobre valor no arreglo
    def report_array_error(self, environment, array_type):

        description = ("Se intento acceder por indice a un valor que no es arreglo, " f"se recibio '{array_type}'")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta tipo de indice incorrecto
    def report_index_type_error(self, environment, index_type):

        description = ("El indice de un arreglo debe ser i32, " f"se recibio '{index_type}'")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta indice fuera de rango
    def report_index_range_error(self, environment, index, size):

        description = (f"Indice {index} fuera de rango para arreglo de tamaño {size}")

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