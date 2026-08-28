from ..node import Node

from ...interpreter.symbol import Symbol
from ...interpreter.types import Types
from ...interpreter.result import Result


class FunctionDeclaration(Node):

    def __init__(self, name, parameters, return_type, instructions, line, column):
        super().__init__(line, column)

        self.name = name
        self.parameters = parameters
        self.instructions = instructions

        self.return_type = Types.VOID
        self.return_element_type = None
        self.return_size = None

        if return_type is not None:

            # Tipo completo enviado por parser
            if isinstance(return_type, dict):
                self.return_type = return_type.get("data_type", Types.VOID)
                self.return_element_type = return_type.get("element_type")
                self.return_size = return_type.get("size")

            # Tipo simple
            else:
                self.return_type = return_type


    # Guarda funcion
    def execute(self, environment):

        # Valida funcion duplicada
        if environment.exists_local(self.name):
            self.report_error(environment, f"Funcion '{self.name}' ya declarada")

            return Result.normal()

        # Valida parametros
        if not self.validate_parameters(environment):
            return Result.normal()

        # Valida tipo de retorno
        if not self.valid_return_type(environment):
            self.report_error(environment, f"Tipo de retorno '{self.return_type}' no valido para funcion '{self.name}'")

            return Result.normal()

        symbol = Symbol(self.name, self, self.return_type, False, "function", self.return_element_type, self.return_size, None, self.line, self.column)

        if not environment.save(symbol):
            self.report_error(environment, f"No se pudo registrar la funcion '{self.name}'")

        return Result.normal()


    # Ejecuta llamada
    def call(self, argument_values, environment):

        # Valida cantidad
        if len(argument_values) != len(self.parameters):
            self.report_error(environment, f"La funcion '{self.name}' esperaba {len(self.parameters)} argumentos y se recibieron {len(argument_values)}")

            return None

        function_environment = environment.create_child(f"function:{self.name}")

        # Guarda parametros
        for index in range(len(self.parameters)):
            parameter = self.parameters[index]
            parameter_name = parameter["name"]
            parameter_type = parameter["data_type"]
            element_type = parameter.get("element_type")
            parameter_size = parameter.get("size")
            value = argument_values[index]
            struct_name = None

            # Parametro struct
            parameter_struct = environment.get(parameter_type)

            if parameter_struct is not None and parameter_struct.kind == "struct":
                if not Types.is_struct_value(value):
                    self.report_error(environment, f"El parametro '{parameter_name}' requiere struct '{parameter_type}'")

                    return None

                if value["struct_name"] != parameter_type:
                    self.report_error(environment, f"El parametro '{parameter_name}' requiere struct '{parameter_type}' y recibio '{value['struct_name']}'")

                    return None

                struct_name = parameter_type

            # Promocion i32 a f64
            elif parameter_type == Types.F64 and Types.get_type(value) == Types.I32:
                value = float(value)

            # Parametro array
            if parameter_type == Types.ARRAY:
                if not isinstance(value, list):
                    self.report_error(environment, f"El parametro '{parameter_name}' requiere un arreglo")

                    return None

                parameter_size = len(value)

                if element_type is not None:
                    if not self.validate_array_values(value, element_type, environment):
                        self.report_error(environment, f"El arreglo recibido en '{parameter_name}' contiene tipos incompatibles")

                        return None


            # Parametro slice
            if parameter_type == Types.SLICE:
                if not Types.is_slice_value(value):
                    self.report_error(environment, f"El parametro '{parameter_name}' requiere un slice")

                    return None

                parameter_size = (value["end"] - value["start"])

            parameter_symbol = Symbol(parameter_name, value, parameter_type, False, "parameter", element_type, parameter_size, struct_name, self.line, self.column)

            if not function_environment.save(parameter_symbol):
                self.report_error(environment, f"Parametro duplicado '{parameter_name}' en funcion '{self.name}'")

                return None

        result = self.execute_block(function_environment)

        # Break fuera de ciclo
        if result.is_break():
            self.report_error(environment, f"Sentencia break fuera de ciclo en funcion '{self.name}'")

            return None

        # Continue fuera de ciclo
        if result.is_continue():
            self.report_error(
                environment,
                f"Sentencia continue fuera de ciclo en funcion '{self.name}'"
            )

            return None


        # Funcion void
        if self.return_type == Types.VOID:

            if result.is_return() and result.value is not None:

                self.report_error(
                    environment,
                    f"La funcion '{self.name}' no debe retornar un valor"
                )


            return None


        # Funcion debe retornar
        if not result.is_return():

            self.report_error(
                environment,
                f"La funcion '{self.name}' debe retornar un valor de tipo '{self.return_type}'"
            )

            return None


        returned_type = self.get_runtime_type(
            result.value
        )


        # Valida tipo de retorno
        if not self.return_type_compatible(
            self.return_type,
            returned_type,
            result.value,
            environment
        ):

            self.report_error(
                environment,
                f"La funcion '{self.name}' debe retornar '{self.return_type}' y retorno '{returned_type}'"
            )

            return None


        # Valida tipo interno de array retornado
        if self.return_type == Types.ARRAY and self.return_element_type is not None:

            if not self.validate_array_values(
                result.value,
                self.return_element_type,
                environment
            ):

                self.report_error(
                    environment,
                    f"La funcion '{self.name}' retorno un arreglo con tipos incompatibles"
                )

                return None


        # Valida tamaño de array retornado
        if self.return_type == Types.ARRAY and self.return_size is not None:

            if len(result.value) != self.return_size:

                self.report_error(
                    environment,
                    f"La funcion '{self.name}' debe retornar un arreglo de tamaño {self.return_size}"
                )

                return None


        # Promocion retorno i32 a f64
        if self.return_type == Types.F64 and returned_type == Types.I32:
            return float(result.value)


        return result.value


    # Ejecuta cuerpo
    def execute_block(self, environment):

        for instruction in self.instructions:

            result = instruction.execute(
                environment
            )


            if result is None:
                continue


            if not result.is_normal():
                return result


        return Result.normal()


    # Valida parametros
    def validate_parameters(self, environment):

        names = []


        for parameter in self.parameters:

            name = parameter["name"]
            data_type = parameter["data_type"]

            element_type = parameter.get("element_type")


            # Parametro duplicado
            if name in names:

                self.report_error(
                    environment,
                    f"Parametro duplicado '{name}' en funcion '{self.name}'"
                )

                return False


            names.append(name)


            # Void no puede ser parametro
            if data_type == Types.VOID:

                self.report_error(environment, f"El parametro '{name}' de funcion '{self.name}' no puede ser void"
                )

                return False


            # Valida tipo
            if not self.valid_parameter_type(
                data_type,
                element_type,
                environment
            ):

                self.report_error(
                    environment,
                    f"Tipo '{data_type}' no valido para parametro '{name}' de funcion '{self.name}'"
                )

                return False


        return True


    # Valida tipo de parametro
    def valid_parameter_type(self, data_type, element_type, environment):

        simple_types = (
            Types.I32,
            Types.F64,
            Types.BOOL,
            Types.CHAR,
            Types.STRING
        )


        if data_type in simple_types:
            return True


        if data_type == Types.ARRAY or data_type == Types.SLICE:

            if element_type is None:
                return True


            return self.valid_element_type(
                element_type,
                environment
            )


        struct_symbol = environment.get(
            data_type
        )


        return (
            struct_symbol is not None
            and struct_symbol.kind == "struct"
        )


    # Valida tipo interno
    def valid_element_type(self, element_type, environment):

        if element_type in (
            Types.I32,
            Types.F64,
            Types.BOOL,
            Types.CHAR,
            Types.STRING
        ):
            return True


        struct_symbol = environment.get(
            element_type
        )


        return (
            struct_symbol is not None
            and struct_symbol.kind == "struct"
        )


    # Valida tipo de retorno
    def valid_return_type(self, environment):

        if self.return_type == Types.VOID:
            return True


        return self.valid_parameter_type(
            self.return_type,
            self.return_element_type,
            environment
        )


    # Obtiene tipo runtime
    def get_runtime_type(self, value):

        # Python no distingue char y String
        if (
            isinstance(value, str)
            and len(value) == 1
            and self.return_type == Types.CHAR
        ):
            return Types.CHAR


        return Types.get_type(
            value
        )


    # Valida retorno
    def return_type_compatible(self, expected, received, value, environment):

        if Types.compatible(expected, received):
            return True


        expected_symbol = environment.get(
            expected
        )


        # Retorno struct
        if expected_symbol is not None and expected_symbol.kind == "struct":

            if received != Types.STRUCT:
                return False


            if not Types.is_struct_value(value):
                return False


            return value["struct_name"] == expected


        return False


    # Valida elementos de array
    def validate_array_values(self, values, element_type, environment):

        if not isinstance(values, list):
            return False


        for value in values:

            value_type = Types.get_type(value)


            # Corrige char
            if (
                element_type == Types.CHAR
                and isinstance(value, str)
                and len(value) == 1
            ):
                value_type = Types.CHAR


            # Struct dentro de array
            struct_symbol = environment.get(
                element_type
            )


            if struct_symbol is not None and struct_symbol.kind == "struct":

                if not Types.is_struct_value(value):
                    return False


                if value["struct_name"] != element_type:
                    return False


                continue


            if not Types.compatible(
                element_type,
                value_type
            ):
                return False


        return True


    # Devuelve tipo parametro
    def get_parameter_type(self, index):

        if index < 0 or index >= len(self.parameters):
            return Types.UNKNOWN


        return self.parameters[index][
            "data_type"
        ]


    # Devuelve tipo interno del parametro
    def get_parameter_element_type(self, index):

        if index < 0 or index >= len(self.parameters):
            return None


        return self.parameters[index].get(
            "element_type"
        )


    # Devuelve tamaño del parametro
    def get_parameter_size(self, index):

        if index < 0 or index >= len(self.parameters):
            return None


        return self.parameters[index].get(
            "size"
        )


    # Cantidad parametros
    def get_parameter_count(self):

        return len(
            self.parameters
        )


    # Reporta error
    def report_error(self, environment, description):

        if self.error_exists(
            environment,
            description
        ):
            return


        environment.semantic_error(
            description,
            self.line,
            self.column
        )


    # Evita error duplicado
    def error_exists(self, environment, description):

        if environment.error_manager is None:
            return False


        for error in environment.error_manager.get_errors():

            if (
                error.error_type == environment.error_manager.SEMANTIC
                and error.description == description
                and error.line == self.line
                and error.column == self.column
            ):
                return True


        return False