from ..errors.error_manager import ErrorManager
from .environment import Environment, Symbol
from .types import SCALARS, array_type, compatible, from_info, name, width


class SemanticAnalyzer:
    def __init__(self, source):
        self.source = source.splitlines()
        self.errors = ErrorManager()
        self.types = {}
        self.bindings = {}
        self.declarations = {}
        self.parameters = {}
        self.functions = {}
        self.returns = {}
        self.frames = {}
        self.symbols = []
        self.loops = []
        self.offset = 0
        self.return_type = 'void'

    def error(self, node, message):
        line = getattr(node, 'line', 0)
        fragment = self.source[line - 1] if 0 < line <= len(self.source) else ''
        self.errors.semantic(message, line, getattr(node, 'column', 0), fragment)

    def check_type(self, node, value):
        if array_type(value):
            if value[2] is not None and (value[2] < 0 or value[2] > 8388608 or width(value) > 64 * 1024 * 1024):
                self.error(node, 'Dimensiones del arreglo exceden el límite del Heap')
            self.check_type(node, value[1])
        elif value not in SCALARS or value == 'void':
            self.error(node, f'Tipo no disponible en OxigenNative: {name(value)}')

    def analyze(self, nodes):
        for node in nodes:
            kind = type(node).__name__
            if kind not in ('MainFunction', 'FunctionDeclaration'):
                self.error(node, 'Solo se compilan declaraciones de funciones en el ámbito global')
                continue
            function_name = getattr(node, 'name', 'main')
            if function_name in self.functions:
                self.error(node, f'Función duplicada: {function_name}')
                continue
            self.functions[function_name] = node
            result = from_info(getattr(node, 'return_info', getattr(node, 'return_type', 'void')))
            if result == 'array':
                result = ('array', from_info(node.return_element_type), node.return_size)
            self.returns[function_name] = result
            if result != 'void':
                self.check_type(node, result)
            self.symbols.append(Symbol(function_name, result, False, 0, 'global', node.line, node.column, True, 'function'))
        if 'main' not in self.functions:
            self.error(nodes[0] if nodes else None, 'No se encontró la función main')
        for function_name, node in self.functions.items():
            self.offset = 0
            self.return_type = self.returns[function_name]
            env = Environment(name=function_name)
            params = []
            for param in getattr(node, 'parameters', []):
                data_type = from_info(param.get('type_info', param))
                self.check_type(node, data_type)
                if param['name'] in env.symbols:
                    self.error(node, f'Parámetro duplicado: {param["name"]}')
                params.append(self.save(node, env, param['name'], data_type, False, True, 'parameter'))
            self.parameters[function_name] = params
            self.block(node.instructions, env, child=False)
            if self.return_type != 'void' and not self.always_returns(node.instructions):
                self.error(node, f'La función {function_name} debe retornar en todas sus rutas')
            self.frames[function_name] = (self.offset + 15) // 16 * 16
        return not self.errors.has_errors()

    def always_returns(self, nodes):
        for node in nodes:
            kind = type(node).__name__
            if kind == 'ReturnInstruction':
                return True
            if kind == 'BlockInstruction' and self.always_returns(node.instructions):
                return True
            if kind == 'IfInstruction' and self.always_returns(node.instructions) and self.always_returns(node.else_instructions):
                return True
            if kind == 'MatchInstruction' and all(self.always_returns([arm['instruction']]) for arm in node.arms):
                return True
        return False

    def save(self, node, env, symbol_name, data_type, mutable, initialized=True, kind='variable'):
        self.offset += 8
        symbol = Symbol(symbol_name, data_type, mutable, self.offset, env.name, node.line, node.column, initialized, kind)
        env.save(symbol)
        self.symbols.append(symbol)
        return symbol

    def block(self, nodes, env, child=True):
        if child:
            env = Environment(env, env.name + '/bloque')
        for node in nodes:
            self.statement(node, env)

    def statement(self, node, env):
        kind = type(node).__name__
        if kind in ('Declaration', 'SliceDeclaration', 'ArrayDeclaration'):
            expression = getattr(node, 'expression', None)
            if kind == 'ArrayDeclaration':
                from ..ast.expressions.array_literal import ArrayLiteral
                expression = ArrayLiteral(node.expressions, node.line, node.column, node.size if node.repeat else None)
                self.declarations[id(node)] = expression
            actual = self.expression(expression, env) if expression else 'unknown'
            declared = from_info(getattr(node, 'type_info', getattr(node, 'data_type', None)))
            if kind == 'ArrayDeclaration' and node.element_type:
                declared = ('array', from_info(node.element_type), node.size)
            if declared == 'unknown':
                declared = actual
            if declared in ('void', 'unknown') or array_type(declared) and declared[1] == 'unknown':
                self.error(node, f'No se puede inferir un tipo válido para {node.name}')
            if expression and array_type(declared) and type(expression).__name__ == 'ArrayLiteral':
                actual = self.coerce_array(expression, declared)
            if expression and not compatible(declared, actual):
                self.error(node, f'Declaración incompatible: {name(declared)} y {name(actual)}')
            self.check_type(node, declared)
            initialized = expression is not None
            if not initialized:
                self.error(node, f'{node.name} requiere un valor inicial')
            symbol = self.save(node, env, node.name, declared, node.mutable, initialized)
            self.bindings[id(node)] = symbol
        elif kind == 'Assignment':
            expected = self.expression(node.target, env)
            actual = self.expression(node.expression, env)
            if array_type(expected) and type(node.expression).__name__ == 'ArrayLiteral':
                actual = self.coerce_array(node.expression, expected)
            base = node.target
            while hasattr(base, 'array'):
                base = base.array
            symbol = env.get(getattr(base, 'name', ''))
            if symbol and not symbol.mutable:
                self.error(node, f'La variable {symbol.name} es inmutable')
            if node.operator != '=':
                actual = self.binary_type(node, expected, actual, node.operator[0])
            if not compatible(expected, actual):
                self.error(node, f'Asignación incompatible: {name(expected)} y {name(actual)}')
        elif kind == 'PrintInstruction':
            if self.expression(node.expression, env) != 'String':
                self.error(node, 'println! requiere formato String')
            for argument in node.arguments:
                if self.expression(argument, env) == 'void':
                    self.error(argument, 'No se puede imprimir void')
            if type(node.expression).__name__ != 'Literal':
                self.error(node, 'El formato de println! debe ser un literal')
            elif node.expression.value.count('{}') != len(node.arguments):
                self.error(node, 'Cantidad de marcadores de println! incompatible')
        elif kind == 'IfInstruction':
            if self.expression(node.condition, env) != 'bool':
                self.error(node, 'La condición debe ser bool')
            self.block(node.instructions, env)
            self.block(node.else_instructions, env)
        elif kind in ('WhileInstruction', 'LoopInstruction'):
            if kind == 'WhileInstruction' and self.expression(node.condition, env) != 'bool':
                self.error(node, 'La condición debe ser bool')
            self.loops.append(node.label)
            self.block(node.instructions, env)
            self.loops.pop()
        elif kind in ('BreakInstruction', 'ContinueInstruction'):
            if not self.loops or node.label is not None and node.label not in self.loops:
                self.error(node, 'Transferencia fuera de ciclo o etiqueta inexistente')
        elif kind == 'ReturnInstruction':
            actual = self.expression(node.expression, env) if node.expression else 'void'
            if array_type(self.return_type) and type(node.expression).__name__ == 'ArrayLiteral':
                actual = self.coerce_array(node.expression, self.return_type)
            if not compatible(self.return_type, actual):
                self.error(node, f'Retorno incompatible: se esperaba {name(self.return_type)}, se recibió {name(actual)}')
        elif kind == 'BlockInstruction':
            self.block(node.instructions, env)
        elif kind == 'MatchInstruction':
            target = self.expression(node.expression, env)
            for arm in node.arms:
                if not arm['default']:
                    pattern = self.expression(arm['pattern'], env)
                    self.compare_type(node, target, pattern)
                self.block([arm['instruction']], env)
        elif kind == 'ExpressionInstruction':
            self.expression(node.expression, env)
        else:
            self.error(node, f'Instrucción no compilable: {kind}')

    def expression(self, node, env):
        if node is None:
            return 'unknown'
        kind = type(node).__name__
        result = 'unknown'
        if kind == 'Literal':
            result = node.data_type
            if result == 'char' and len(node.value) != 1:
                self.error(node, 'El literal char debe contener un único carácter válido')
            if result in ('String', 'char') and '\0' in node.value:
                self.error(node, 'No se admite NUL en literales de texto')
            if result == 'i32' and not -2147483648 <= node.value <= 2147483647:
                self.error(node, 'Literal fuera del rango i32')
        elif kind == 'Identifier':
            symbol = env.get(node.name)
            if symbol is None:
                self.error(node, f'Variable no declarada: {node.name}')
            else:
                self.bindings[id(node)] = symbol
                result = symbol.data_type
                if not symbol.initialized:
                    self.error(node, f'Variable sin inicializar: {node.name}')
        elif kind == 'ArrayLiteral':
            values = [self.expression(value, env) for value in node.expressions]
            element = values[0] if values else 'unknown'
            for value in values:
                if value == 'f64' and element == 'i32':
                    element = 'f64'
                if not compatible(element, value):
                    self.error(node, 'El arreglo debe ser homogéneo y rectangular')
            result = ('array', element, node.repeat if node.repeat is not None else len(values))
        elif kind in ('Arithmetic', 'Relational', 'Logical'):
            left = self.expression(node.left, env)
            right = self.expression(node.right, env)
            if kind == 'Arithmetic':
                result = self.binary_type(node, left, right, node.operator)
            elif kind == 'Logical':
                if left != 'bool' or right != 'bool':
                    self.error(node, 'Operador lógico requiere bool')
                result = 'bool'
            else:
                self.compare_type(node, left, right)
                result = 'bool'
        elif kind == 'Unary':
            #el mínimo i32 se permite con signo unario
            if node.operator == '-' and type(node.expression).__name__ == 'Literal' and node.expression.value == 2147483648:
                self.types[id(node.expression)] = 'i32'
                result = 'i32'
            else:
                result = self.expression(node.expression, env)
                if node.operator == '!' and result != 'bool' or node.operator == '-' and result not in ('i32', 'f64'):
                    self.error(node, 'Operando unario incompatible')
        elif kind in ('ArrayAccess', 'SliceAccess'):
            target = self.expression(node.array, env)
            indices = [node.index] if kind == 'ArrayAccess' else [node.start, node.end]
            for index in indices:
                if self.expression(index, env) != 'i32':
                    self.error(index, 'El índice debe ser i32')
            if not array_type(target):
                self.error(node, 'El acceso requiere un arreglo o slice')
            else:
                result = target[1] if kind == 'ArrayAccess' else ('slice', target[1], None)
                constant = self.constant_int(node.index) if kind == 'ArrayAccess' else None
                if kind == 'ArrayAccess' and constant is not None and target[2] is not None:
                    if constant < 0 or constant >= target[2]:
                        self.error(node, 'Índice fuera de los límites del arreglo')
                if kind == 'SliceAccess' and all(type(index).__name__ == 'Literal' for index in indices):
                    start, end = node.start.value, node.end.value
                    if start < 0 or end < start or target[2] is not None and end > target[2]:
                        self.error(node, 'Rango de slice fuera de los límites')
        elif kind == 'FunctionCall':
            values = [self.expression(arg, env) for arg in node.arguments]
            function = self.functions.get(node.name)
            if function is None or node.name == 'main':
                self.error(node, f'Función no declarada o no invocable: {node.name}')
            else:
                params = getattr(function, 'parameters', [])
                if len(values) != len(params):
                    self.error(node, f'Cantidad de argumentos incorrecta en {node.name}')
                for param, value, argument in zip(params, values, node.arguments):
                    expected = from_info(param.get('type_info', param))
                    if array_type(expected) and type(argument).__name__ == 'ArrayLiteral':
                        value = self.coerce_array(argument, expected)
                    if not compatible(expected, value):
                        self.error(node, f'Tipo de argumento incompatible en {node.name}')
                result = self.returns[node.name]
        elif kind == 'NativeCall':
            result = self.native(node, env)
        else:
            self.error(node, f'Expresión no compilable: {kind}')
        self.types[id(node)] = result
        return result

    def constant_int(self, node):
        kind = type(node).__name__
        if kind == 'Literal' and node.data_type == 'i32':
            return node.value
        if kind == 'Unary' and node.operator == '-':
            value = self.constant_int(node.expression)
            return -value if value is not None else None
        if kind == 'Arithmetic' and node.operator in ('+', '-', '*'):
            left, right = self.constant_int(node.left), self.constant_int(node.right)
            if left is not None and right is not None:
                return {'+': lambda: left + right, '-': lambda: left - right, '*': lambda: left * right}[node.operator]()
        return None

    def coerce_array(self, node, expected):
        actual = self.types[id(node)]
        if actual[2] != expected[2]:
            return actual
        for expression in node.expressions:
            value = self.types[id(expression)]
            if array_type(expected[1]) and type(expression).__name__ == 'ArrayLiteral':
                value = self.coerce_array(expression, expected[1])
            if not compatible(expected[1], value):
                return actual
        self.types[id(node)] = expected
        return expected

    def binary_type(self, node, left, right, operator):
        if left in ('i32', 'f64') and right in ('i32', 'f64'):
            return 'f64' if 'f64' in (left, right) else 'i32'
        if operator == '+' and left == right == 'String':
            return 'String'
        if operator == '*' and (left, right) in (('String', 'i32'), ('i32', 'String')):
            return 'String'
        self.error(node, f'Operación {operator} incompatible entre {name(left)} y {name(right)}')
        return 'unknown'

    def compare_type(self, node, left, right):
        valid = left == right and left in ('i32', 'f64', 'bool', 'char', 'String')
        valid = valid or left in ('i32', 'f64') and right in ('i32', 'f64') or (left, right) in (('i32', 'char'), ('char', 'i32'))
        if not valid:
            self.error(node, f'Comparación incompatible entre {name(left)} y {name(right)}')

    def native(self, node, env):
        target = self.expression(node.target, env) if node.target else None
        args = [self.expression(arg, env) for arg in node.arguments]
        method = node.name
        counts = {'String::new': 0, 'String::from': 1, 'typeof': 1, 'random': 2, 'len': 0, 'contains': 1, 'replace': 2, 'split': 1, 'to_uppercase': 0, 'to_lowercase': 0, 'reverse': 0, 'clone': 0, 'chars': 0, 'abs': 1, 'sqrt': 1}
        if method not in counts or len(args) != counts.get(method):
            self.error(node, f'Nativa desconocida o cantidad de argumentos incorrecta: {method}')
            return 'unknown'
        if method in ('String::new', 'String::from', 'typeof'):
            if method == 'String::from' and args[0] == 'void':
                self.error(node, 'String::from no acepta void')
            return 'String'
        if method == 'random':
            if args != ['i32', 'i32']:
                self.error(node, 'random requiere dos i32')
            return 'i32'
        if method in ('abs', 'sqrt'):
            if args[0] not in ('i32', 'f64'):
                self.error(node, f'{method} requiere un número')
            return 'f64' if method == 'sqrt' else args[0]
        if target is None:
            self.error(node, f'{method} requiere un receptor')
            return 'unknown'
        if method == 'clone':
            return target
        if method == 'len' and (target == 'String' or array_type(target)):
            return 'i32'
        if method == 'contains':
            if target == 'String' and args[0] in ('String', 'char') or array_type(target) and compatible(target[1], args[0]):
                return 'bool'
        if method in ('replace', 'split', 'to_uppercase', 'to_lowercase', 'chars') and target == 'String':
            if any(value != 'String' for value in args):
                self.error(node, f'{method} requiere argumentos String')
            return ('array', 'String', None) if method == 'split' else ('array', 'char', None) if method == 'chars' else 'String'
        if method == 'reverse' and array_type(target):
            base = node.target
            while hasattr(base, 'array'):
                base = base.array
            symbol = env.get(getattr(base, 'name', ''))
            if symbol is None or not symbol.mutable:
                self.error(node, 'reverse requiere un arreglo mutable')
            return target
        self.error(node, f'Receptor o argumentos incompatibles en {method}')
        return 'unknown'
