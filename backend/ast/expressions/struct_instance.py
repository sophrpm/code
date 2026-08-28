from ..node import Node

from ...interpreter.types import Types


class StructInstance(Node):

    def __init__(self, struct_name, fields, line, column):
        super().__init__(line, column)

        self.struct_name = struct_name
        self.fields = fields


    #instancia de struct
    def evaluate(self, environment):

        struct_symbol = environment.get(self.struct_name)

        #existe?
        if struct_symbol is None:
            self.report_struct_not_found(environment)
            return None

        #es struct?
        if struct_symbol.kind != "struct":
            self.report_not_struct(environment)
            return None

        struct_definition = struct_symbol.value

        #cantidad de campos
        if len(self.fields) != len(struct_definition):
            self.report_field_count_error(environment, len(struct_definition), len(self.fields))

            return None

        values = {}

        for field in self.fields:

            field_name = field["name"]
            expression = field["expression"]

            #campo existente
            if field_name not in struct_definition:
                self.report_field_not_found(environment, field_name)
                return None

            #campo repetido
            if field_name in values:
                self.report_duplicate_field(environment, field_name)
                return None

            expected_type = struct_definition[field_name]
            received_type = expression.get_type(environment)

            #tipo
            if not self.types_compatible(expected_type, received_type, expression, environment):
                self.report_type_error(environment, field_name, expected_type, received_type)

                return None

            value = expression.evaluate(environment)

            if value is None:
                return None

            #convierte i32 a f64
            if (expected_type == Types.F64 and received_type == Types.I32):
                value = float(value)

            values[field_name] = value

        #campos faltantes
        for field_name in struct_definition:

            if field_name not in values:
                self.report_missing_field(environment, field_name)
                return None

        return {
            "struct_name": self.struct_name,
            "fields": values
        }


    #tipo general
    def get_type(self, environment):

        struct_symbol = environment.get(self.struct_name)

        if struct_symbol is None:
            return Types.UNKNOWN

        if struct_symbol.kind != "struct":
            return Types.UNKNOWN

        return Types.STRUCT


    #nombre especifico
    def get_struct_name(self, environment=None):

        return self.struct_name

    # Valida instancia
    def validate(self, environment):

        struct_symbol = environment.get(self.struct_name)

        if struct_symbol is None:
            self.report_struct_not_found(environment)
            return False

        if struct_symbol.kind != "struct":
            self.report_not_struct(environment)
            return False

        struct_definition = struct_symbol.value

        if len(self.fields) != len(struct_definition):

            self.report_field_count_error(environment, len(struct_definition), len(self.fields))

            return False

        used_fields = []

        for field in self.fields:
            field_name = field["name"]
            expression = field["expression"]

            if field_name not in struct_definition:
                self.report_field_not_found(environment, field_name)
                return False

            if field_name in used_fields:
                self.report_duplicate_field(environment, field_name)
                return False

            used_fields.append(field_name)
            expected_type = struct_definition[field_name]
            received_type = expression.get_type(environment)

            if not self.types_compatible(expected_type, received_type, expression, environment):
                self.report_type_error(environment, field_name, expected_type, received_type)

                return False

        for field_name in struct_definition:

            if field_name not in used_fields:
                self.report_missing_field(environment, field_name)
                return False

        return True


    #compatibilidad de tipos
    def types_compatible(self, expected_type, received_type, expression, environment):

        #normal
        if Types.compatible(expected_type, received_type):
            return True


        #struct dentro de otro struct
        if received_type == Types.STRUCT:
            if not hasattr(expression, "get_struct_name"):
                return False

            received_struct = expression.get_struct_name(environment)

            return expected_type == received_struct

        return False


    #reporta struct inexistente
    def report_struct_not_found(self, environment):

        description = f"Struct '{self.struct_name}' no declarado"

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta simbolo que no es struct
    def report_not_struct(self, environment):

        description = f"'{self.struct_name}' no es un struct"

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta cantidad incorrecta
    def report_field_count_error(self, environment, expected, received):

        description = (f"El struct '{self.struct_name}' requiere {expected} campos, " f"se recibieron {received}")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta campo inexistente
    def report_field_not_found(self, environment, field_name):

        description = (f"El campo '{field_name}' no existe en " f"el struct '{self.struct_name}'")

        if self.error_exists(environment, description):
            return

        environment.semantic_error( description, self.line, self.column)


    # Reporta campo repetido
    def report_duplicate_field(self, environment, field_name):

        description = (f"El campo '{field_name}' esta repetido en " f"la instancia de '{self.struct_name}'")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta campo faltante
    def report_missing_field(self, environment, field_name):

        description = (f"Falta el campo '{field_name}' en " f"la instancia de '{self.struct_name}'")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    # Reporta tipo incompatible
    def report_type_error(self, environment, field_name, expected_type, received_type):

        description = (f"Tipo incompatible para el campo '{field_name}' de " f"'{self.struct_name}': se esperaba '{expected_type}' " f"y se recibio '{received_type}'")

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    #error duplicado
    def error_exists(self, environment, description):

        if environment.error_manager is None:
            return False

        for error in environment.error_manager.get_errors():
            if (error.error_type == environment.error_manager.SEMANTIC and error.description == description and error.line == self.line and error.column == self.column):
                return True

        return False