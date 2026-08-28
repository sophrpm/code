from ..node import Node

from ...interpreter.types import Types


class Logical(Node):

    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)

        self.left = left
        self.operator = operator
        self.right = right


    # Evalua operacion logica
    def evaluate(self, environment):

        left_type = self.left.get_type(environment)
        right_type = self.right.get_type(environment)

        if not self.validate_types(left_type, right_type):
            self.report_type_error(environment, left_type, right_type)
            return None

        left_value = self.left.evaluate(environment)

        if left_value is None:
            return None

        #corto circuito AND
        if self.operator == "&&":
            if left_value is False:
                return False

            right_value = self.right.evaluate(environment)

            if right_value is None:
                return None

            return right_value

        #corto circuito OR
        if self.operator == "||":
            if left_value is True:
                return True

            right_value = self.right.evaluate(environment)

            if right_value is None:
                return None

            return right_value

        environment.semantic_error(f"Operador logico '{self.operator}' no reconocido", self.line, self.column)

        return None


    #tipo del resultado
    def get_type(self, environment):

        left_type = self.left.get_type(environment)
        right_type = self.right.get_type(environment)

        if not self.validate_types(left_type, right_type):
            return Types.UNKNOWN

        return Types.BOOL


    # Valida expresion
    def validate(self, environment):

        left_type = self.left.get_type(environment)
        right_type = self.right.get_type(environment)

        if self.validate_types(left_type, right_type):
            return True

        self.report_type_error(environment, left_type, right_type)

        return False


    # Valida tipos
    def validate_types(self, left_type, right_type):

        if self.operator != "&&" and self.operator != "||":
            return False

        return (left_type == Types.BOOL and right_type == Types.BOOL)


    #reporta tipos incompatibles
    def report_type_error(self, environment, left_type, right_type):

        description = (f"Operacion logica '{self.operator}' requiere valores bool, " f"se recibio '{left_type}' y '{right_type}'")

        if environment.error_manager is not None:
            for error in environment.error_manager.get_errors():
                if (error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column):
                    return

        environment.semantic_error(description, self.line, self.column)