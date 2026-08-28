# ast/instructions/print_instruction.py

from ..node import Node
from ...interpreter.types import Types
from ...interpreter.result import Result


class PrintInstruction(Node):

    def __init__(self, expression, arguments, line, column):
        super().__init__(line, column)
        self.expression = expression
        self.arguments = arguments

    # Ejecuta println
    def execute(self, environment):
        if self.expression is None:
            self.report_error(environment, "println necesita una expresion de formato")
            return Result.normal()

        expression_type = self.expression.get_type(environment)
        if expression_type != Types.STRING:
            self.report_error(environment, f"println requiere String como formato, se recibio '{expression_type}'")
            return Result.normal()

        text = self.expression.evaluate(environment)
        if text is None:
            return Result.normal()

        placeholders = text.count("{}")
        if placeholders != len(self.arguments):
            self.report_error(environment, f"println contiene {placeholders} espacios de formato y recibio {len(self.arguments)} argumentos")
            return Result.normal()

        result = text

        for argument in self.arguments:
            value = argument.evaluate(environment)
            if value is None and argument.get_type(environment) != Types.VOID:
                return Result.normal()
            result = result.replace("{}", self.format_value(value), 1)

        environment.write_console(result)
        return Result.normal()

    # Convierte valor para impresion
    def format_value(self, value):
        if value is None:
            return "None"

        if isinstance(value, bool):
            if value:
                return "true"
            return "false"

        if isinstance(value, list):
            values = []
            for item in value:
                if isinstance(item, str):
                    values.append('"' + item.replace('"', '\\"') + '"')
                else:
                    values.append(self.format_value(item))
            return "[" + ", ".join(values) + "]"

        if Types.is_slice_value(value):
            array = value["array"]
            start = value["start"]
            end = value["end"]
            values = []
            for index in range(start, end):
                values.append(self.format_value(array[index]))
            return "[" + ", ".join(values) + "]"

        if Types.is_struct_value(value):
            fields = value["fields"]
            values = []
            for field_name in fields:
                values.append(field_name + ": " + self.format_value(fields[field_name]))
            return value["struct_name"] + " { " + ", ".join(values) + " }"

        return str(value)

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
