from dataclasses import dataclass


@dataclass
class Symbol:
    name: str
    data_type: object
    mutable: bool
    offset: int
    scope: str
    line: int
    column: int
    initialized: bool = True
    kind: str = 'variable'


class Environment:
    def __init__(self, parent=None, name='global'):
        self.parent = parent
        self.name = name
        self.symbols = {}

    def get(self, name):
        if name in self.symbols:
            return self.symbols[name]
        return self.parent.get(name) if self.parent else None

    def save(self, symbol):
        self.symbols[symbol.name] = symbol
