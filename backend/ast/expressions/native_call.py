# ast/expressions/native_call.py

import random

from ..node import Node
from .identifier import Identifier

from ...interpreter.types import Types

from ...natives import (string_from, len_function, abs_function, sqrt_function, clone_function, chars_function, contains_function, array_push, array_remove)


class NativeCall(Node):

    def __init__(self, name, arguments, line, column, target=None):
        super().__init__(line, column)

        self.name = name
        self.arguments = arguments
        self.target = target


    # Evalua llamada nativa
    def evaluate(self, environment):

        if not self.validate(environment):
            return None


        # typeof usa el tipo del AST
        if self.name == "typeof":
            return self.evaluate_typeof(environment)

        arguments = []

        for argument in self.arguments:
            value = argument.evaluate(environment)

            if value is None and argument.get_type(environment) != Types.VOID:
                return None

            arguments.append(value)

        target_value = None

        if self.target is not None:
            target_value = self.target.evaluate(environment)

            if target_value is None:
                return None

        # String::from
        if self.name == "String::from":
            return string_from(arguments[0])

        # String::new
        if self.name == "String::new":
            return ""

        # random
        if self.name == "random":

            minimum = arguments[0]
            maximum = arguments[1]

            if minimum > maximum:
                self.report_error(environment, "El valor minimo de random no puede ser mayor al maximo")

                return None

            return random.randint(minimum, maximum)

        # len
        if self.name == "len":
            return len_function(target_value)

        # abs
        if self.name == "abs":
            return abs_function(arguments[0])

        # sqrt
        if self.name == "sqrt":
            if arguments[0] < 0:
                self.report_error(environment, "sqrt no acepta valores negativos")

                return None

            return sqrt_function(arguments[0])

        # clone
        if self.name == "clone":
            return clone_function(target_value)

        # chars
        if self.name == "chars":
            return chars_function(target_value)

        # contains
        if self.name == "contains":
            return contains_function(target_value, arguments[0])

        # replace
        if self.name == "replace":
            return target_value.replace(arguments[0], arguments[1])

        # split
        if self.name == "split":
            return target_value.split(arguments[0])

        # to_uppercase
        if self.name == "to_uppercase":
            return target_value.upper()

        # to_lowercase
        if self.name == "to_lowercase":
            return target_value.lower()

        # reverse
        if self.name == "reverse":

            if not self.validate_mutable_array(environment):
                return None

            target_value.reverse()
            return target_value

        # push
        if self.name == "push":
            if not self.validate_mutable_array(environment):
                return None

            result = array_push(target_value, arguments[0])

            if result is None:
                self.report_error(environment, "No se pudo agregar el valor al arreglo")

                return None

            self.update_array_size(environment)

            return result

        # remove
        if self.name == "remove":
            if not self.validate_mutable_array(environment):
                return None
            index = arguments[0]

            if index < 0 or index >= len(target_value):
                self.report_error(environment, f"Indice {index} fuera de rango para arreglo de tamaño {len(target_value)}")

                return None

            result = array_remove(target_value, index)
            self.update_array_size(environment)

            return result


        self.report_error(environment, f"Funcion nativa '{self.name}' no reconocida")

        return None


    # Devuelve tipo del resultado
    def get_type(self, environment):

        if self.name == "String::from":
            return Types.STRING

        if self.name == "String::new":
            return Types.STRING

        if self.name == "typeof":
            return Types.STRING
        
        if self.name == "random":
            return Types.I32

        if self.name == "len":
            return Types.I32

        if self.name == "abs":
            if len(self.arguments) != 1:
                return Types.UNKNOWN

            return self.arguments[0].get_type(environment)

        if self.name == "sqrt":
            return Types.F64

        if self.name == "clone":
            if self.target is None:
                return Types.UNKNOWN

            return self.target.get_type(environment)

        if self.name == "chars":
            return Types.ARRAY

        if self.name == "contains":
            return Types.BOOL

        if self.name == "replace":
            return Types.STRING

        if self.name == "split":
            return Types.ARRAY

        if self.name == "to_uppercase":
            return Types.STRING

        if self.name == "to_lowercase":
            return Types.STRING

        if self.name == "reverse":
            return Types.ARRAY

        if self.name == "push":
            return Types.ARRAY

        if self.name == "remove":
            return self.get_array_element_type(environment)

        return Types.UNKNOWN


    # Devuelve tipo interno de arreglo
    def get_element_type(self, environment):

        if self.name == "chars":
            return Types.CHAR

        if self.name == "split":
            return Types.STRING

        if self.name == "clone":
            if self.target is None:
                return None

            if hasattr(self.target, "get_element_type"):
                return self.target.get_element_type(environment)

        if self.name == "reverse":
            return self.get_array_element_type(environment)

        if self.name == "push":
            return self.get_array_element_type(environment)

        return None


    # Valida llamada
    def validate(self, environment):

        if self.name == "String::from":
            if self.target is not None or len(self.arguments) != 1:
                self.report_error(environment, "String::from requiere un argumento")
                return False

            return True

        if self.name == "String::new":
            if self.target is not None or len(self.arguments) != 0:
                self.report_error(environment, "String::new no recibe argumentos")
                return False

            return True

        if self.name == "typeof":
            if self.target is not None or len(self.arguments) != 1:
                self.report_error(environment, "typeof requiere un argumento")
                return False

            return True

        if self.name == "random":
            if self.target is not None or len(self.arguments) != 2:
                self.report_error(environment, "random requiere dos argumentos")

                return False

            first_type = self.arguments[0].get_type(environment)
            second_type = self.arguments[1].get_type(environment)

            if first_type != Types.I32 or second_type != Types.I32:
                self.report_error(environment, "random requiere dos valores i32")

                return False

            return True

        if self.name == "len":
            if not self.validate_target(environment, 0):
                return False

            target_type = self.target.get_type(environment)

            if (target_type != Types.STRING and target_type != Types.ARRAY and target_type != Types.SLICE):
                self.report_error(environment, "len solo puede utilizarse con String, array o slice")

                return False

            return True


        if self.name == "abs" or self.name == "sqrt":
            if self.target is not None or len(self.arguments) != 1:
                self.report_error(environment, f"{self.name} requiere un argumento")

                return False

            argument_type = self.arguments[0].get_type(environment)

            if not Types.is_numeric(argument_type):
                self.report_error(environment, f"{self.name} requiere un valor numerico")

                return False

            return True

        if self.name == "clone":
            if not self.validate_target(environment, 0):
                return False

            return True

        if self.name == "chars":
            if not self.validate_target(environment, 0):
                return False

            if self.target.get_type(environment) != Types.STRING:
                self.report_error(environment, "chars solo puede utilizarse con String")

                return False

            return True

        if self.name == "contains":
            if not self.validate_target(environment, 1):
                return False

            target_type = self.target.get_type(environment)

            if target_type == Types.STRING:
                argument_type = self.arguments[0].get_type(environment)

                if argument_type != Types.STRING and argument_type != Types.CHAR:
                    self.report_error(environment, "contains en String requiere String o char")

                    return False

                return True

            if target_type == Types.ARRAY or target_type == Types.SLICE:
                element_type = self.get_array_element_type(environment)
                argument_type = self.arguments[0].get_type(environment)

                if element_type is not None and not Types.compatible(element_type, argument_type):
                    self.report_error(environment, f"contains esperaba '{element_type}' y recibio '{argument_type}'")

                    return False

                return True

            self.report_error(environment, "contains solo puede utilizarse con String, array o slice")

            return False

        if self.name == "replace":
            if not self.validate_string_method(environment, 2):
                return False

            first_type = self.arguments[0].get_type(environment)
            second_type = self.arguments[1].get_type(environment)

            if first_type != Types.STRING or second_type != Types.STRING:
                self.report_error(environment, "replace requiere dos argumentos String")

                return False

            return True

        if self.name == "split":
            if not self.validate_string_method(environment, 1):
                return False

            if self.arguments[0].get_type(environment) != Types.STRING:
                self.report_error(environment, "split requiere un argumento String")

                return False

            return True

        if self.name == "to_uppercase" or self.name == "to_lowercase":
            return self.validate_string_method(environment, 0)

        if self.name == "reverse":
            if not self.validate_target(environment, 0):
                return False

            if self.target.get_type(environment) != Types.ARRAY:
                self.report_error(environment, "reverse solo puede utilizarse con arreglos")

                return False

            return True

        if self.name == "push":
            if not self.validate_target(environment, 1):
                return False

            if self.target.get_type(environment) != Types.ARRAY:
                self.report_error(environment, "push solo puede utilizarse con arreglos")

                return False

            element_type = self.get_array_element_type(environment)
            value_type = self.arguments[0].get_type(environment)

            if element_type is None:
                self.report_error(environment, "No se pudo determinar el tipo del arreglo")

                return False

            if not Types.compatible(element_type, value_type):
                self.report_error(environment, f"push esperaba '{element_type}' y recibio '{value_type}'")

                return False

            return True

        if self.name == "remove":
            if not self.validate_target(environment, 1):
                return False

            if self.target.get_type(environment) != Types.ARRAY:
                self.report_error(environment, "remove solo puede utilizarse con arreglos")

                return False

            if self.arguments[0].get_type(environment) != Types.I32:
                self.report_error(environment, "remove requiere un indice i32")

                return False

            return True

        self.report_error(environment, f"Funcion nativa '{self.name}' no reconocida")

        return False

    # Valida metodo con target
    def validate_target(self, environment, argument_count):
        if self.target is None:
            self.report_error(environment, f"'{self.name}' requiere un valor objetivo")

            return False

        if len(self.arguments) != argument_count:
            self.report_error(environment, f"'{self.name}' requiere {argument_count} argumentos")

            return False

        target_type = self.target.get_type(environment)

        if target_type == Types.UNKNOWN:
            return False

        return True


    # Valida metodo String
    def validate_string_method(self, environment, argument_count):

        if not self.validate_target(environment, argument_count):
            return False
        
        if self.target.get_type(environment) != Types.STRING:
            self.report_error(environment, f"'{self.name}' solo puede utilizarse con String")

            return False

        return True


    # Obtiene tipo interno de array o slice
    def get_array_element_type(self, environment):

        if self.target is None:
            return None

        if hasattr(self.target, "get_element_type"):
            return self.target.get_element_type(environment)

        if isinstance(self.target, Identifier):

            symbol = environment.get(self.target.name)
            if symbol is None:
                return None

            return symbol.element_type

        return None


    # Valida arreglo mutable
    def validate_mutable_array(self, environment):

        if not isinstance(self.target, Identifier):
            self.report_error(environment, f"'{self.name}' requiere una variable de arreglo")

            return False

        symbol = environment.get(self.target.name)

        if symbol is None:
            return False

        if symbol.data_type != Types.ARRAY:
            self.report_error(environment, f"'{self.name}' solo puede utilizarse con arreglos")

            return False

        if not symbol.mutable:

            self.report_error(environment, f"El arreglo '{symbol.name}' es inmutable")

            return False

        return True


    # Actualiza tamaño del arreglo
    def update_array_size(self, environment):

        if not isinstance(self.target, Identifier):
            return

        symbol = environment.get(self.target.name)

        if symbol is None:
            return

        if isinstance(symbol.value, list):
            symbol.size = len(symbol.value)


    # Evalua typeof
    def evaluate_typeof(self, environment):

        argument = self.arguments[0]
        data_type = argument.get_type(environment)

        if data_type == Types.STRUCT and hasattr(argument, "get_struct_name"):
            struct_name = argument.get_struct_name(environment)

            if struct_name is not None:
                return struct_name

        return Types.to_string(data_type)


    # Reporta error semantico
    def report_error(self, environment, description):

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