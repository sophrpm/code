from ..node import Node
from ..expressions.identifier import Identifier
from ..expressions.array_access import ArrayAccess
from ..expressions.struct_access import StructAccess
from ...interpreter.types import Types
from ...interpreter.result import Result


class Assignment(Node):

    def __init__(self, target, operator, expression, line, column):
        super().__init__(line, column)
        self.target = target
        self.operator = operator
        self.expression = expression

    # Ejecuta asignacion
    def execute(self, environment):
        symbol = self.get_base_symbol(self.target, environment)

        if symbol is None:
            self.report_error(environment, "No se encontro la variable de la asignacion")
            return Result.normal()

        if not symbol.mutable:
            self.report_error(environment, f"La variable '{symbol.name}' es inmutable")
            return Result.normal()

        value_type = self.expression.get_type(environment)
        if value_type == Types.UNKNOWN:
            return Result.normal()

        value = self.expression.evaluate(environment)
        if value is None and value_type != Types.VOID:
            return Result.normal()

        if isinstance(self.target, Identifier):
            self.assign_identifier(symbol, value, value_type, environment)
            return Result.normal()

        if isinstance(self.target, ArrayAccess):
            self.assign_array(symbol, value, value_type, environment)
            return Result.normal()

        if isinstance(self.target, StructAccess):
            self.assign_struct(value, value_type, environment)
            return Result.normal()

        self.report_error(environment, "El lado izquierdo de la asignacion no es valido")
        return Result.normal()

    # Asigna variable
    def assign_identifier(self, symbol, value, value_type, environment):
        current_type = symbol.data_type

        if self.operator == "=":
            if not self.types_compatible(current_type, value_type, self.expression, environment, symbol.struct_name):
                self.report_error(environment, f"No se puede asignar '{value_type}' a '{current_type}'")
                return

            if current_type == Types.F64 and value_type == Types.I32:
                value = float(value)

            symbol.value = value
            return

        if symbol.struct_name is not None:
            self.report_error(environment, "Los structs no permiten operadores de asignacion compuesta")
            return

        success, new_value, new_type = self.apply_operator(symbol.value, current_type, value, value_type, environment)
        if not success:
            return

        if not Types.compatible(current_type, new_type):
            self.report_error(environment, f"El resultado '{new_type}' no puede guardarse en '{current_type}'")
            return

        if current_type == Types.F64 and new_type == Types.I32:
            new_value = float(new_value)

        symbol.value = new_value

    # Asigna posicion de arreglo
    def assign_array(self, symbol, value, value_type, environment):
        if symbol.data_type != Types.ARRAY:
            self.report_error(environment, f"'{symbol.name}' no es un arreglo")
            return

        if symbol.element_type is None:
            self.report_error(environment, f"No se conoce el tipo interno del arreglo '{symbol.name}'")
            return

        index_type = self.target.index.get_type(environment)
        if index_type != Types.I32:
            self.report_error(environment, f"El indice del arreglo debe ser i32, se recibio '{index_type}'")
            return

        array_value = self.target.array.evaluate(environment)
        index_value = self.target.index.evaluate(environment)

        if array_value is None or index_value is None:
            return

        if index_value < 0 or index_value >= len(array_value):
            self.report_error(environment, f"Indice {index_value} fuera de rango para arreglo de tamaño {len(array_value)}")
            return

        element_type = symbol.element_type
        current_value = array_value[index_value]

        if self.operator == "=":
            if not self.types_compatible(element_type, value_type, self.expression, environment):
                self.report_error(environment, f"El arreglo esperaba '{element_type}' y se recibio '{value_type}'")
                return

            if element_type == Types.F64 and value_type == Types.I32:
                value = float(value)

            array_value[index_value] = value
            return

        success, new_value, new_type = self.apply_operator(current_value, element_type, value, value_type, environment)
        if not success:
            return

        if not Types.compatible(element_type, new_type):
            self.report_error(environment, f"El resultado '{new_type}' no puede guardarse en un arreglo de '{element_type}'")
            return

        if element_type == Types.F64 and new_type == Types.I32:
            new_value = float(new_value)

        array_value[index_value] = new_value

    # Asigna campo de struct
    def assign_struct(self, value, value_type, environment):
        if not self.target.validate(environment):
            return

        struct_value = self.target.struct.evaluate(environment)
        if struct_value is None:
            return

        fields = struct_value["fields"]
        expected_type = self.target.get_type(environment)
        if expected_type == Types.UNKNOWN:
            return

        current_value = fields[self.target.field]

        if self.operator == "=":
            expected_struct = self.target.get_struct_name(environment)

            if expected_struct is not None:
                if not self.types_compatible(expected_struct, value_type, self.expression, environment, expected_struct):
                    self.report_error(environment, f"El campo '{self.target.field}' requiere struct '{expected_struct}'")
                    return
            elif not Types.compatible(expected_type, value_type):
                self.report_error(environment, f"El campo '{self.target.field}' esperaba '{expected_type}' y se recibio '{value_type}'")
                return

            if expected_type == Types.F64 and value_type == Types.I32:
                value = float(value)

            fields[self.target.field] = value
            return

        if self.target.get_struct_name(environment) is not None:
            self.report_error(environment, "Los campos struct no permiten asignacion compuesta")
            return

        success, new_value, new_type = self.apply_operator(current_value, expected_type, value, value_type, environment)
        if not success:
            return

        if not Types.compatible(expected_type, new_type):
            self.report_error(environment, f"El resultado '{new_type}' no puede guardarse en el campo '{self.target.field}'")
            return

        if expected_type == Types.F64 and new_type == Types.I32:
            new_value = float(new_value)

        fields[self.target.field] = new_value

    # Aplica operador compuesto
    def apply_operator(self, left_value, left_type, right_value, right_type, environment):
        if self.operator == "+=":
            if left_type == Types.STRING and right_type == Types.STRING:
                return True, left_value + right_value, Types.STRING
            if Types.is_numeric(left_type) and Types.is_numeric(right_type):
                return True, left_value + right_value, self.numeric_result_type(left_type, right_type)
            self.report_operator_error(environment, left_type, right_type)
            return False, None, Types.UNKNOWN

        if self.operator == "-=":
            if not self.numeric_types(left_type, right_type):
                self.report_operator_error(environment, left_type, right_type)
                return False, None, Types.UNKNOWN
            return True, left_value - right_value, self.numeric_result_type(left_type, right_type)

        if self.operator == "*=":
            if left_type == Types.STRING and right_type == Types.I32:
                if right_value < 0:
                    self.report_error(environment, "No se puede repetir un String una cantidad negativa de veces")
                    return False, None, Types.UNKNOWN
                return True, left_value * right_value, Types.STRING

            if not self.numeric_types(left_type, right_type):
                self.report_operator_error(environment, left_type, right_type)
                return False, None, Types.UNKNOWN

            return True, left_value * right_value, self.numeric_result_type(left_type, right_type)

        if self.operator == "/=":
            if not self.numeric_types(left_type, right_type):
                self.report_operator_error(environment, left_type, right_type)
                return False, None, Types.UNKNOWN
            if right_value == 0:
                self.report_error(environment, "Division entre cero")
                return False, None, Types.UNKNOWN
            if left_type == Types.I32 and right_type == Types.I32:
                return True, int(left_value / right_value), Types.I32
            return True, left_value / right_value, Types.F64

        if self.operator == "%=":
            if not self.numeric_types(left_type, right_type):
                self.report_operator_error(environment, left_type, right_type)
                return False, None, Types.UNKNOWN
            if right_value == 0:
                self.report_error(environment, "Modulo entre cero")
                return False, None, Types.UNKNOWN
            return True, left_value % right_value, self.numeric_result_type(left_type, right_type)

        self.report_error(environment, f"Operador de asignacion '{self.operator}' no reconocido")
        return False, None, Types.UNKNOWN

    # Compatibilidad incluyendo structs
    def types_compatible(self, expected_type, received_type, expression, environment, expected_struct=None):
        if Types.compatible(expected_type, received_type):
            return True

        struct_symbol = environment.get(expected_type)
        if struct_symbol is not None and struct_symbol.kind == "struct":
            if received_type != Types.STRUCT or not hasattr(expression, "get_struct_name"):
                return False
            return expression.get_struct_name(environment) == expected_type

        if expected_struct is not None and received_type == Types.STRUCT:
            if not hasattr(expression, "get_struct_name"):
                return False
            return expression.get_struct_name(environment) == expected_struct

        return False

    # Tipo numerico resultante
    def numeric_result_type(self, left_type, right_type):
        if left_type == Types.F64 or right_type == Types.F64:
            return Types.F64
        return Types.I32

    # Valida tipos numericos
    def numeric_types(self, left_type, right_type):
        return Types.is_numeric(left_type) and Types.is_numeric(right_type)

    # Busca simbolo principal
    def get_base_symbol(self, target, environment):
        if isinstance(target, Identifier):
            return environment.get(target.name)
        if isinstance(target, ArrayAccess):
            return self.get_base_symbol(target.array, environment)
        if isinstance(target, StructAccess):
            return self.get_base_symbol(target.struct, environment)
        return None

    # Reporta operador invalido
    def report_operator_error(self, environment, left_type, right_type):
        self.report_error(environment, f"Operacion '{self.operator}' no permitida entre '{left_type}' y '{right_type}'")

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
