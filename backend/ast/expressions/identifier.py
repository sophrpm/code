from ..node import Node

from ...interpreter.types import Types


class Identifier(Node):

    def __init__(self, name, line, column):
        super().__init__(line, column)

        self.name = name


    #valor del simbolo
    def evaluate(self, environment):

        symbol = environment.get(self.name)
        if symbol is None:
            self.report_not_found(environment)

            return None

        return symbol.value


    #tipo del simbolo
    def get_type(self, environment):

        symbol = environment.get(self.name)
        if symbol is None:
            self.report_not_found(environment)

            return Types.UNKNOWN

        return symbol.data_type


    #simbolo completo
    def get_symbol(self, environment):

        symbol = environment.get(self.name)
        if symbol is None:
            self.report_not_found(environment)

        return symbol


    #nombre especifico del struct
    def get_struct_name(self, environment):

        symbol = environment.get(self.name)
        if symbol is None:
            self.report_not_found(environment)

            return None

        return symbol.struct_name


    #tipo interno de array o slice
    def get_element_type(self, environment):

        symbol = environment.get(self.name)
        if symbol is None:
            self.report_not_found(environment)

            return None

        if symbol.data_type != Types.ARRAY and symbol.data_type != Types.SLICE:
            return None

        return symbol.element_type


    #si existe
    def validate(self, environment):

        if environment.exists(self.name):
            return True

        self.report_not_found(environment)

        return False


    #valor a texto
    def to_string(self, environment):

        value = self.evaluate(environment)
        if value is None:
            return ""

        if isinstance(value, bool):
            if value:
                return "true"

            return "false"

        return str(value)


    #Reporta identificador inexistente
    def report_not_found(self, environment):
        description = f"Identificador '{self.name}' no declarado"

        #aca me aseguro que no se registre el mismo error varias veces
        if environment.error_manager is not None:
            for error in environment.error_manager.get_errors():
                if (error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column):
                    return

        environment.semantic_error(description, self.line, self.column)