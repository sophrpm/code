# ast/expressions/relational.py

from ..node import Node

from ...interpreter.types import Types


class Relational(Node):

    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)

        self.left = left
        self.operator = operator
        self.right = right


    #operacion relacional
    def evaluate(self, environment):

        left_type = self.left.get_type(environment)
        right_type = self.right.get_type(environment)

        if not self.validate_types(left_type, right_type):
            self.report_type_error(environment, left_type, right_type)
            return None

        left_value = self.left.evaluate(environment)
        right_value = self.right.evaluate(environment)

        if left_value is None or right_value is None:
            return None

        if self.operator == "==":
            return left_value == right_value

        if self.operator == "!=":
            return left_value != right_value

        if self.operator == ">":
            return left_value > right_value

        if self.operator == ">=":
            return left_value >= right_value

        if self.operator == "<":
            return left_value < right_value

        if self.operator == "<=":
            return left_value <= right_value

        environment.semantic_error(f"Operador relacional '{self.operator}' no reconocido", self.line, self.column)

        return None


    #tipo del resultado
    def get_type(self, environment):

        left_type = self.left.get_type(environment)
        right_type = self.right.get_type(environment)

        if not self.validate_types(left_type, right_type):
            return Types.UNKNOWN

        return Types.BOOL


    #valida expresion
    def validate(self, environment):

        left_type = self.left.get_type(environment)
        right_type = self.right.get_type(environment)

        if self.validate_types(left_type, right_type):
            return True

        self.report_type_error(environment, left_type, right_type)

        return False


    #tipos segun operador
    def validate_types(self, left_type, right_type):

        if self.operator == "==" or self.operator == "!=":
            return self.validate_equality_types(left_type, right_type)

        if (self.operator == ">" or self.operator == ">=" or self.operator == "<" or self.operator == "<="):
            return self.validate_order_types(left_type, right_type)

        return False


    #igualdad
    def validate_equality_types(self, left_type, right_type):

        if left_type == right_type:
            return True

        if (Types.is_numeric(left_type) and Types.is_numeric(right_type)):
            return True

        return False


    #comparaciones de orden
    def validate_order_types(self, left_type, right_type):

        if (Types.is_numeric(left_type) and Types.is_numeric(right_type)):
            return True

        if (left_type == Types.CHAR and right_type == Types.CHAR):
            return True

        return False


    #reporta tipos incompatibles
    def report_type_error(self, environment, left_type, right_type):

        description = (f"Comparacion '{self.operator}' no permitida entre " f"'{left_type}' y '{right_type}'")

        if environment.error_manager is not None:
            for error in environment.error_manager.get_errors():
                if (error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column):
                    return

        environment.semantic_error(description, self.line, self.column)