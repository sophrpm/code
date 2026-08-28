class Environment:

    def __init__(self, parent=None, name="global", error_manager=None, history=None):
        self.parent = parent
        self.name = name
        self.symbols = []
        self.children = []

        if error_manager is not None:
            self.error_manager = error_manager
        elif parent is not None:
            self.error_manager = parent.error_manager
        else:
            self.error_manager = None

        if history is not None:
            self.history = history
        elif parent is not None:
            self.history = parent.history
        else:
            self.history = []

        self.history.append(self)


    #simbolo en entorno actual
    def save(self, symbol, allow_shadowing=False):

        current_symbol = self.get_local(symbol.name)
        if current_symbol is not None:
            if not allow_shadowing:
                return False

            if current_symbol.kind != "variable":
                return False

            if symbol.kind != "variable":
                return False

        self.symbols.append(symbol)

        return True


    #buscamos simbolo actual mas reciente
    def get_local(self, name):

        for symbol in reversed(self.symbols):

            if symbol.name == name:
                return symbol

        return None


    #buscsmos en entorno actual y padres
    def get(self, name):

        symbol = self.get_local(name)

        if symbol is not None:
            return symbol

        if self.parent is not None:
            return self.parent.get(name)

        return None


    #simbolo en todos los entornos
    def exists(self, name):

        return self.get(name) is not None


    #simbolo en entorno actual
    def exists_local(self, name):

        return self.get_local(name) is not None


    #actualiza simbolo existente
    def update(self, name, value):

        symbol = self.get_local(name)

        if symbol is not None:
            symbol.value = value
            return True

        if self.parent is not None:
            return self.parent.update(name, value)

        return False


    #simbolos del entorno
    def get_symbols(self):

        return self.symbols


    #scopes hijos
    def get_children(self):

        return self.children


    #historial completo de scopes
    def get_history(self):

        return self.history


    #entorno hijo
    def create_child(self, name="scope"):

        child = Environment(self, name, self.error_manager, self.history)
        self.children.append(child)
        return child


    #error semantico
    def semantic_error(self, description, line, column, fragment=None):

        if self.error_manager is None:
            return

        self.error_manager.semantic(description, line, column, fragment)
