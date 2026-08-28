from ..node import Node

from ...interpreter.types import Types


class Arithmetic(Node):

    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)

        self.left = left
        self.operator = operator
        self.right = right


    #operacion aritmetica
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

        if self.operator == "+":
            return left_value + right_value

        if self.operator == "-":
            return left_value - right_value

        if self.operator == "*":

            #string * i32
            if left_type == Types.STRING and right_type == Types.I32:
                if right_value < 0:
                    environment.semantic_error("No se puede repetir un String una cantidad negativa de veces", self.line, self.column)

                    return None

                return left_value * right_value

            return left_value * right_value

        if self.operator == "/":
            if right_value == 0:
                environment.semantic_error("Division entre cero", self.line, self.column)

                return None

            # i32 / i32
            if left_type == Types.I32 and right_type == Types.I32:
                return int(left_value / right_value)

            return left_value / right_value

        if self.operator == "%":
            if right_value == 0:
                environment.semantic_error("Modulo entre cero", self.line, self.column)

                return None

            return left_value % right_value

        environment.semantic_error(f"Operador aritmetico '{self.operator}' no reconocido", self.line, self.column)

        return None


    #tipo del resultado
    def get_type(self, environment):

        left_type = self.left.get_type(environment)
        right_type = self.right.get_type(environment)

        if not self.validate_types(left_type, right_type):
            return Types.UNKNOWN

        #String + String
        if ( self.operator == "+" and left_type == Types.STRING and right_type == Types.STRING):
            return Types.STRING

        # String * i32
        if (self.operator == "*" and left_type == Types.STRING and right_type == Types.I32):
            return Types.STRING

        #division entre i32
        if (self.operator == "/" and left_type == Types.I32 and right_type == Types.I32):
            return Types.I32

        #promocion a f64
        if left_type == Types.F64 or right_type == Types.F64:
            return Types.F64

        return Types.I32


    #expresion
    def validate(self, environment):

        left_type = self.left.get_type(environment)
        right_type = self.right.get_type(environment)

        if self.validate_types(left_type, right_type):
            return True

        self.report_type_error(environment, left_type, right_type)

        return False


    #tipos segun operador
    def validate_types(self, left_type, right_type):

        if self.operator == "+":
            if left_type == Types.STRING and right_type == Types.STRING:
                return True
            
            return (Types.is_numeric(left_type) and Types.is_numeric(right_type))

        if self.operator == "-":
            return (Types.is_numeric(left_type) and Types.is_numeric(right_type))

        if self.operator == "*":

            if left_type == Types.STRING and right_type == Types.I32:
                return True

            return (Types.is_numeric(left_type) and Types.is_numeric(right_type))

        if self.operator == "/":
            return (Types.is_numeric(left_type) and Types.is_numeric(right_type))

        if self.operator == "%":
            return (Types.is_numeric(left_type) and Types.is_numeric(right_type))

        return False


    #tipos incompatibles
    def report_type_error(self, environment, left_type, right_type):

        description = (f"Operacion '{self.operator}' no permitida entre " f"'{left_type}' y '{right_type}'")

        if environment.error_manager is not None:
            for error in environment.error_manager.get_errors():
                if (error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column):
                    return

        environment.semantic_error(description, self.line, self.column)