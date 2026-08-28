from .error import Error

class ErrorManager:

    LEXICAL = "Lexico"
    SYNTACTIC = "Sintactico"
    SEMANTIC = "Semantico"

    def __init__(self):
        self.errors = []


    #error generico
    def add(self, error_type, description, line, column, fragment=None):

        error = Error(error_type, description, line, column, fragment)
        self.errors.append(error)


    #error lexico
    def lexical(self, description, line, column, fragment=None):

        self.add(self.LEXICAL, description, line, column, fragment)


    #error sintactico
    def syntactic(self, description, line, column, fragment=None):

        self.add(self.SYNTACTIC, description, line, column, fragment)


    #error semantico
    def semantic(self, description, line, column, fragment=None):

        self.add(self.SEMANTIC, description, line, column, fragment)


    #error ya creado
    def add_error(self, error):

        if isinstance(error, Error):
            self.errors.append(error)


    #errores
    def get_errors(self):

        return self.errors


    #errores como diccionarios
    def to_list(self):

        result = []
        for error in self.errors:
            result.append(error.to_dict())

        return result


    #existen errores?
    def has_errors(self):

        return len(self.errors) > 0


    # Limpia errores
    def clear(self):

        self.errors.clear()


    #cantidad de errores
    def count(self):

        return len(self.errors)


    #cantidad por tipo
    def count_by_type(self, error_type):

        count = 0
        for error in self.errors:
            if error.error_type == error_type:
                count += 1

        return count