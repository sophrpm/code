# ast/expressions/struct_access.py

from ..node import Node

from ...interpreter.types import Types


class StructAccess(Node):

    def __init__(self, struct, field, line, column):
        super().__init__(line, column)

        self.struct = struct
        self.field = field


    # Evalua acceso a campo
    def evaluate(self, environment):

        struct_name = self.get_base_struct_name(environment)

        if struct_name is None:
            self.report_struct_error(environment)
            return None

        struct_symbol = environment.get(struct_name)

        if struct_symbol is None or struct_symbol.kind != "struct":
            self.report_struct_error(environment)
            return None

        struct_value = self.struct.evaluate(environment)

        if struct_value is None:
            return None

        if not Types.is_struct_value(struct_value):
            self.report_struct_error(environment)
            return None

        fields = struct_value["fields"]

        if self.field not in fields:
            self.report_field_error(environment, struct_name)
            return None

        return fields[self.field]


    # Devuelve tipo del campo
    def get_type(self, environment):

        struct_name = self.get_base_struct_name(environment)

        if struct_name is None:
            return Types.UNKNOWN

        struct_symbol = environment.get(struct_name)

        if struct_symbol is None:
            return Types.UNKNOWN

        if struct_symbol.kind != "struct":
            return Types.UNKNOWN

        struct_definition = struct_symbol.value

        if self.field not in struct_definition:
            return Types.UNKNOWN

        field_type = struct_definition[self.field]

        field_symbol = environment.get(field_type)

        #campo que es otro struct
        if field_symbol is not None and field_symbol.kind == "struct":
            return Types.STRUCT

        return field_type


    #nombre del struct base
    def get_base_struct_name(self, environment):

        # Nodo que ya conoce su struct
        if hasattr(self.struct, "get_struct_name"):

            struct_name = self.struct.get_struct_name(environment)

            if struct_name is not None:
                return struct_name

        #ID normal
        if hasattr(self.struct, "name"):

            symbol = environment.get(self.struct.name)

            if symbol is None:
                return None

            return symbol.struct_name

        return None


    #nombre del struct del campo
    def get_struct_name(self, environment):

        base_struct_name = self.get_base_struct_name(environment)

        if base_struct_name is None:
            return None

        struct_symbol = environment.get(base_struct_name)

        if struct_symbol is None:
            return None

        if struct_symbol.kind != "struct":
            return None

        struct_definition = struct_symbol.value

        if self.field not in struct_definition:
            return None

        field_type = struct_definition[self.field]

        field_symbol = environment.get(field_type)

        if field_symbol is None:
            return None

        if field_symbol.kind != "struct":
            return None

        return field_type


    # Valida acceso
    def validate(self, environment):

        struct_name = self.get_base_struct_name(environment)

        if struct_name is None:
            self.report_struct_error(environment)
            return False

        struct_symbol = environment.get(struct_name)

        if struct_symbol is None or struct_symbol.kind != "struct":
            self.report_struct_error(environment)
            return False

        struct_definition = struct_symbol.value

        if self.field not in struct_definition:
            self.report_field_error(environment, struct_name)
            return False

        return True


    #acceso sobre valor no struct
    def report_struct_error(self, environment):

        description = "Se intento acceder a un campo de un valor que no es struct"

        if self.error_exists(environment, description):
            return

        environment.semantic_error(description, self.line, self.column)


    #campo inexistente
    def report_field_error(self, environment, struct_name):

        description = (f"El campo '{self.field}' no existe en el struct '{struct_name}'")

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