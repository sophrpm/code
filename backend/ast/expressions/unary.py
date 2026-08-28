from ..node import Node

from ...interpreter.types import Types


class Unary(Node):

    def __init__(self, operator, expression, line, column):
        super().__init__(line, column)

        self.operator = operator
        self.expression = expression


    #evalua operacion unaria
    def evaluate(self, environment):

        expression_type = self.expression.get_type(environment)

        if not self.validate_type(expression_type):
            self.report_type_error(environment, expression_type)
            return None

        value = self.expression.evaluate(environment)

        if value is None:
            return None

        #negacion numerica
        if self.operator == "-":
            return -value

        #negacion logica
        if self.operator == "!":
            return not value

        environment.semantic_error(f"Operador unario '{self.operator}' no reconocido", self.line, self.column)

        return None

    #devuelve tipo del resultado
    def get_type(self, environment):

        expression_type = self.expression.get_type(environment)

        if not self.validate_type(expression_type):
            return Types.UNKNOWN

        if self.operator == "-":
            return expression_type

        if self.operator == "!":
            return Types.BOOL

        return Types.UNKNOWN


    #expresion
    def validate(self, environment):

        expression_type = self.expression.get_type(environment)

        if self.validate_type(expression_type):
            return True

        self.report_type_error(environment, expression_type)

        return False


    #tipo segun operador
    def validate_type(self, expression_type):

        if self.operator == "-":
            return Types.is_numeric(expression_type)

        if self.operator == "!":
            return expression_type == Types.BOOL

        return False


    #tipo incompatible
    def report_type_error(self, environment, expression_type):

        if self.operator == "-":
            description = ("La negacion numerica requiere un valor numerico, " f"se recibio '{expression_type}'")

        elif self.operator == "!":
            description = ("La negacion logica requiere un valor bool, " f"se recibio '{expression_type}'")

        else:
            description = (f"Operador unario '{self.operator}' no reconocido")

        if environment.error_manager is not None:

            for error in environment.error_manager.get_errors():

                if (error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column):
                    return

        environment.semantic_error(description, self.line, self.column)