class Types:

    I32 = "i32"
    F64 = "f64"
    BOOL = "bool"
    CHAR = "char"
    STRING = "String"

    ARRAY = "array"
    SLICE = "slice"
    STRUCT = "struct"

    FUNCTION = "function"
    VOID = "void"
    UNKNOWN = "unknown"


    #tipo de un valor
    @staticmethod
    def get_type(value):

        if value is None:
            return Types.VOID

        if isinstance(value, bool):
            return Types.BOOL

        if isinstance(value, int):
            return Types.I32

        if isinstance(value, float):
            return Types.F64

        if isinstance(value, str):
            return Types.STRING

        if isinstance(value, list):
            return Types.ARRAY

        if isinstance(value, dict):

            if Types.is_slice_value(value):
                return Types.SLICE

            if Types.is_struct_value(value):
                return Types.STRUCT

        return Types.UNKNOWN


    #es numero
    @staticmethod
    def is_numeric(data_type):

        return data_type == Types.I32 or data_type == Types.F64


    #es booleano
    @staticmethod
    def is_boolean(data_type):

        return data_type == Types.BOOL


    #es texto
    @staticmethod
    def is_string(data_type):

        return data_type == Types.STRING


    #es arreglo
    @staticmethod
    def is_array(data_type):

        return data_type == Types.ARRAY


    #es slice
    @staticmethod
    def is_slice(data_type):

        return data_type == Types.SLICE


    #es struct
    @staticmethod
    def is_struct(data_type):

        return data_type == Types.STRUCT


    #valor slice
    @staticmethod
    def is_slice_value(value):

        if not isinstance(value, dict):
            return False

        return ("array" in value and "start" in value and "end" in value)


    #valor struct
    @staticmethod
    def is_struct_value(value):

        if not isinstance(value, dict):
            return False

        return ("struct_name" in value and "fields" in value)


    #compatibilidad de tipos
    @staticmethod
    def compatible(expected, received):

        if expected == received:
            return True
        if expected == Types.F64 and received == Types.I32:
            return True

        return False


    #nombre del tipo
    @staticmethod
    def to_string(data_type):
        if data_type is None:
            return Types.UNKNOWN

        return str(data_type)