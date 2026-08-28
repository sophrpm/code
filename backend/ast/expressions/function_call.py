from ..node import Node

from ...interpreter.types import Types


class FunctionCall(Node):

    def __init__(self, name, arguments, line, column):
        super().__init__(line, column)

        self.name = name
        self.arguments = arguments


    #llamada a funcion
    def evaluate(self, environment):

        function = self.get_function(environment)

        if function is None:
            return None

        if not self.validate_arguments(function, environment):
            return None

        argument_values = []

        for argument in self.arguments:

            value = argument.evaluate(environment)

            #si el argumento produjo error
            if value is None and argument.get_type(environment) != Types.VOID:
                return None

            argument_values.append(value)

        return function.call(argument_values, environment)


    #tipo de retorno
    def get_type(self, environment):

        symbol = environment.get(self.name)

        if symbol is None:
            return Types.UNKNOWN

        if symbol.kind != "function":
            return Types.UNKNOWN

        return symbol.data_type


    #llamada
    def validate(self, environment):

        function = self.get_function(environment)

        if function is None:
            return False

        return self.validate_arguments(function, environment)


    # Obtiene funcion
    def get_function(self, environment):

        symbol = environment.get(self.name)

        #inexistente
        if symbol is None:
            self.report_function_not_found(environment)

            return None

        #no es funcion
        if symbol.kind != "function":
            self.report_not_function(environment)

            return None

        return symbol.value


    #argumentos
    def validate_arguments(self, function, environment):

        expected_count = function.get_parameter_count()
        received_count = len(self.arguments)

        # Cantidad incorrecta
        if expected_count != received_count:
            self.report_argument_count_error(environment, expected_count, received_count)

            return False


        # Tipos de argumentos
        for index in range(received_count):
            argument = self.arguments[index]
            expected_type = function.get_parameter_type(index)
            received_type = argument.get_type(environment)

            if not self.types_compatible( expected_type, received_type, argument, environment):
                self.report_argument_type_error(environment, index, expected_type, received_type)

                return False

        return True


    # Valida compatibilidad
    def types_compatible(self, expected_type, received_type, argument, environment):

        #normal
        if Types.compatible(expected_type, received_type):
            return True

        # Parametro de tipo struct
        expected_symbol = environment.get(expected_type)

        if (expected_symbol is not None and expected_symbol.kind == "struct"):

            if received_type != Types.STRUCT:
                return False

            if not hasattr(argument, "get_struct_name"):
                return False

            received_struct = argument.get_struct_name(environment)

            return expected_type == received_struct

        return False


    #reporta funcion inexistente
    def report_function_not_found(self, environment):

        description = f"Funcion '{self.name}' no declarada"

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    #reporta simbolo que no es funcion
    def report_not_function(self, environment):

        description = f"'{self.name}' no es una funcion"

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta cantidad incorrecta de argumentos
    def report_argument_count_error(self, environment, expected, received):

        description = (f"La funcion '{self.name}' requiere {expected} argumentos, " f"se recibieron {received}")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta tipo incorrecto de argumento
    def report_argument_type_error(self, environment, index, expected, received):

        description = (f"Argumento {index + 1} incompatible en funcion '{self.name}': " f"se esperaba '{expected}' y se recibio '{received}'")

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