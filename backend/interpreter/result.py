# representa el resultado de la ejecucion de una instruccion en modo normal, return, break o continue
class Result:

    NORMAL = "normal"
    RETURN = "return"
    BREAK = "break"
    CONTINUE = "continue"


    def __init__(self,result_type=NORMAL,value=None,label=None):

        self.result_type = result_type
        self.value = value
        self.label = label


    # Verifica si ejecucion continua normal
    def is_normal(self):

        return self.result_type == Result.NORMAL


    # Verifica return
    def is_return(self):

        return self.result_type == Result.RETURN


    # Verifica break
    def is_break(self):

        return self.result_type == Result.BREAK


    # Verifica continue
    def is_continue(self):

        return self.result_type == Result.CONTINUE


    # Crea resultado normal
    @staticmethod
    def normal():

        return Result(Result.NORMAL)


    # Crea resultado return
    @staticmethod
    def return_value(value=None):

        return Result(Result.RETURN, value)


    # Crea resultado break
    @staticmethod
    def break_result(label=None):
        return Result(Result.BREAK, None, label)


    # Crea resultado continue
    @staticmethod
    def continue_result(label=None):
        return Result(Result.CONTINUE, None, label)