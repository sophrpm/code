from .environment import Environment
from .result import Result

from ..errors.error_manager import ErrorManager

from ..ast.instructions.function_declaration import FunctionDeclaration
from ..ast.instructions.struct_declaration import StructDeclaration
from ..ast.instructions.main_function import MainFunction


class Interpreter:

    def __init__(self):
        self.error_manager = ErrorManager()
        self.global_environment = Environment(None, "global", self.error_manager)


    #programa completo
    def execute(self, instructions):

        self.reset()
        main_function = None
        main_count = 0

        if instructions is None:
            return Result.normal()

        # Primera pasada
        #Registra structs y funciones
        for instruction in instructions:
            if instruction is None:
                continue

            #struct
            if isinstance(instruction, StructDeclaration):
                if self.global_environment.exists_local(instruction.name):
                    self.semantic_error(f"Simbolo '{instruction.name}' ya declarado", instruction.line, instruction.column)

                    continue

                instruction.execute(self.global_environment)

                continue

            #funcion normal
            if isinstance(instruction, FunctionDeclaration):
                if self.global_environment.exists_local(instruction.name):
                    self.semantic_error(f"Funcion '{instruction.name}' ya declarada", instruction.line, instruction.column)

                    continue

                instruction.execute(self.global_environment)

                continue

            #main
            if isinstance(instruction, MainFunction):
                main_count += 1

                if main_function is None:
                    main_function = instruction

                continue

            #instruccion invalida en entorno global
            self.semantic_error("Instruccion no permitida en el entorno global", instruction.line, instruction.column)


        #existencia de main
        if main_count == 0:

            self.semantic_error("No se encontro la funcion main", 0, 0)

            return Result.normal()

        #main duplicado
        if main_count > 1:
            self.semantic_error("Solo puede existir una funcion main", main_function.line, main_function.column)

            return Result.normal()

        #conflicto con nombre main
        if self.global_environment.exists_local("main"):
            self.semantic_error("El nombre 'main' ya esta utilizado por otro simbolo", main_function.line, main_function.column)

            return Result.normal()

        #no exc si existen errores previos
        if self.error_manager.has_errors():
            return Result.normal()


        #Segunda pasada
        #Ejecuta main
        result = main_function.execute(self.global_environment)

        if result is None:
            return Result.normal()

        #Break fuera de ciclo
        if result.is_break():

            self.semantic_error("Sentencia break fuera de un ciclo", main_function.line, main_function.column)

            return Result.normal()

        #continue fuera de ciclo
        if result.is_continue():
            self.semantic_error("Sentencia continue fuera de un ciclo", main_function.line, main_function.column)

            return Result.normal()

        #main no debe retornar valor
        if result.is_return():
            if result.value is not None:
                self.semantic_error("La funcion main no puede retornar un valor", main_function.line, main_function.column)

            return Result.normal()

        return result


    #lista de instrucciones
    def execute_block(self, instructions, environment):

        if instructions is None:
            return Result.normal()

        for instruction in instructions:

            if instruction is None:
                continue

            result = instruction.execute(environment)

            if result is None:
                continue

            if not result.is_normal():
                return result

        return Result.normal()


    # Reinicia interprete
    def reset(self):

        self.error_manager.clear()
        self.global_environment = Environment(None, "global", self.error_manager)


    #error semantico
    def semantic_error(self, description, line, column, fragment=None):

        self.error_manager.semantic(description, line, column, fragment)


    #entorno global
    def get_global_environment(self):

        return self.global_environment


    #historial de scopes
    def get_scope_history(self):

        return self.global_environment.get_history()


    #todos los simbolos
    def get_all_symbols(self):

        result = []

        for environment in self.get_scope_history():
            for symbol in environment.get_symbols():
                result.append({
                    "name": symbol.name,
                    "kind": symbol.kind,
                    "data_type": symbol.data_type,
                    "mutable": symbol.mutable,
                    "element_type": symbol.element_type,
                    "size": symbol.size,
                    "struct_name": symbol.struct_name,
                    "scope": environment.name,
                    "line": symbol.line,
                    "column": symbol.column
                })

        return result


    #errores
    def get_errors(self):

        return self.error_manager.to_list()


    def has_errors(self):

        return self.error_manager.has_errors()


    #cantidad de errores
    def get_error_count(self):

        return self.error_manager.count()