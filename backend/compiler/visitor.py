from .generator import Generator
from .types import array_type, from_info


class ARM64Visitor:
    def __init__(self, semantic):
        self.semantic = semantic
        self.g = Generator()
        self.loops = []
        self.return_label = ''

    def data_type(self, node):
        return self.semantic.types[id(node)]

    def emit(self, *lines):
        self.g.emit(*lines)

    def push(self, data_type, register=None):
        register = register or ('d0' if data_type == 'f64' else 'x0')
        self.emit(f'    str {register}, [sp, #-16]!')

    def pop(self, data_type, register=None):
        register = register or ('d0' if data_type == 'f64' else 'x0')
        self.emit(f'    ldr {register}, [sp], #16')

    def convert(self, actual, expected):
        if actual == 'i32' and expected == 'f64':
            self.emit('    scvtf d0, w0')

    def local_address(self, symbol):
        self.g.integer(symbol.offset, 'x9')
        self.emit('    sub x0, x29, x9')

    def generate(self):
        for function_name, node in self.semantic.functions.items():
            self.function(function_name, node)
        return self.g.finish()

    #cada función reserva locales; temporales usan espacios de 16 bytes
    def function(self, function_name, node):
        self.return_label = self.g.label('return')
        label = 'main' if function_name == 'main' else 'ox_fn_' + function_name
        self.emit(f'// función {function_name}: guardar frame pointer y retorno', f'{label}:', '    stp x29, x30, [sp, #-16]!', '    mov x29, sp')
        self.g.integer(self.semantic.frames[function_name], 'x9')
        self.emit('    // reservar locales, tamaño alineado a 16 bytes', '    sub sp, sp, x9')
        self.current_return = self.semantic.returns[function_name]
        integers = floats = stack = 0
        for param in self.semantic.parameters[function_name]:
            self.g.integer(param.offset, 'x9')
            self.emit('    sub x9, x29, x9')
            if param.data_type == 'f64' and floats < 8:
                self.emit(f'    str d{floats}, [x9]')
                floats += 1
            elif param.data_type != 'f64' and integers < 8:
                self.emit(f'    str x{integers}, [x9]')
                integers += 1
            else:
                self.g.integer(16 + stack * 8, 'x10')
                self.emit('    ldr x10, [x29, x10]', '    str x10, [x9]')
                stack += 1
        if function_name == 'main':
            self.emit('    bl ox_init')
        self.block(node.instructions)
        self.emit('    mov x0, #0', self.return_label + ':', '    // restaurar el frame y retornar al llamador', '    mov sp, x29', '    ldp x29, x30, [sp], #16', '    ret')

    def block(self, nodes):
        for node in nodes:
            self.visit(node)

    def visit(self, node):
        kind = type(node).__name__
        if kind in ('Declaration', 'SliceDeclaration', 'ArrayDeclaration'):
            symbol = self.semantic.bindings[id(node)]
            expression = self.semantic.declarations.get(id(node), getattr(node, 'expression', None))
            self.expression(expression)
            self.convert(self.data_type(expression), symbol.data_type)
            self.push(symbol.data_type)
            self.local_address(symbol)
            self.pop(symbol.data_type, 'd1' if symbol.data_type == 'f64' else 'x1')
            self.emit(f'    str {"d1" if symbol.data_type == "f64" else "x1"}, [x0]')
        elif kind == 'Assignment':
            expected = self.data_type(node.target)
            self.address(node.target)
            self.push('i32')
            if node.operator != '=':
                self.emit(f'    ldr {"d0" if expected == "f64" else "x0"}, [x0]')
                self.push(expected)
            self.expression(node.expression)
            actual = self.data_type(node.expression)
            if node.operator != '=':
                actual = self.operation(expected, actual, node.operator[0])
            self.convert(actual, expected)
            if array_type(expected) and type(node.target).__name__ != 'Identifier':
                self.emit('    mov x1, x0')
                self.pop('i32')
                self.emit('    bl ox_copy_array_data')
            else:
                if expected == 'f64':
                    self.emit('    fmov x1, d0')
                else:
                    self.emit('    mov x1, x0')
                self.pop('i32')
                self.emit('    str x1, [x0]')
        elif kind == 'PrintInstruction':
            #evaluamos los argumentos antes de producir la línea
            for argument in node.arguments:
                self.expression(argument)
                self.push(self.data_type(argument))
            pieces = node.expression.value.split('{}')
            for index, piece in enumerate(pieces):
                self.g.string(piece)
                self.emit('    bl ox_print_text')
                if index < len(node.arguments):
                    argument = node.arguments[index]
                    offset = (len(node.arguments) - index - 1) * 16
                    self.g.integer(offset, 'x9')
                    self.emit('    ldr x0, [sp, x9]')
                    self.g.address(self.g.descriptor(self.data_type(argument)), 'x1')
                    self.emit('    bl ox_print')
            if node.arguments:
                self.g.integer(len(node.arguments) * 16, 'x9')
                self.emit('    add sp, sp, x9')
            self.emit('    mov w0, #10', '    bl putchar')
        elif kind == 'IfInstruction':
            otherwise, end = self.g.label('else'), self.g.label('endif')
            self.expression(node.condition)
            self.emit(f'    cbz x0, {otherwise}')
            self.block(node.instructions)
            self.emit(f'    b {end}', otherwise + ':')
            self.block(node.else_instructions)
            self.emit(end + ':')
        elif kind in ('WhileInstruction', 'LoopInstruction'):
            start, end = self.g.label('loop'), self.g.label('endloop')
            self.loops.append((node.label, start, end))
            self.emit(start + ':')
            if kind == 'WhileInstruction':
                self.expression(node.condition)
                self.emit(f'    cbz x0, {end}')
            self.block(node.instructions)
            self.emit(f'    b {start}', end + ':')
            self.loops.pop()
        elif kind in ('BreakInstruction', 'ContinueInstruction'):
            target = next(loop for loop in reversed(self.loops) if node.label is None or node.label == loop[0])
            self.emit(f'    b {target[2] if kind == "BreakInstruction" else target[1]}')
        elif kind == 'ReturnInstruction':
            if node.expression:
                self.expression(node.expression)
                self.convert(self.data_type(node.expression), self.current_return)
            self.emit(f'    b {self.return_label}')
        elif kind == 'BlockInstruction':
            self.block(node.instructions)
        elif kind == 'ExpressionInstruction':
            self.expression(node.expression)
        elif kind == 'MatchInstruction':
            end = self.g.label('endmatch')
            self.expression(node.expression)
            self.push(self.data_type(node.expression))
            for arm in node.arms:
                following = self.g.label('arm')
                if not arm['default']:
                    self.expression(arm['pattern'])
                    left, right = self.data_type(node.expression), self.data_type(arm['pattern'])
                    self.emit('    ldr d1, [sp]' if left == 'f64' else '    ldr x1, [sp]')
                    self.compare(left, right, '==')
                    self.emit(f'    cbz x0, {following}')
                #el temporal del match no debe quedar en sp durante break/continue
                self.emit('    add sp, sp, #16')
                self.visit(arm['instruction'])
                self.emit(f'    b {end}', following + ':')
            self.emit('    add sp, sp, #16', end + ':')

    def expression(self, node):
        kind = type(node).__name__
        data_type = self.data_type(node)
        if kind == 'Literal':
            if data_type == 'String':
                self.g.string(node.value)
                self.emit('    bl ox_string_copy')
            elif data_type == 'f64':
                self.g.floating(node.value)
            else:
                self.g.integer(ord(node.value) if data_type == 'char' else int(node.value))
        elif kind == 'Identifier':
            self.local_address(self.semantic.bindings[id(node)])
            self.emit(f'    ldr {"d0" if data_type == "f64" else "x0"}, [x0]')
        elif kind == 'ArrayLiteral':
            self.g.integer(data_type[2])
            self.g.address(self.g.descriptor(data_type[1]), 'x1')
            self.emit('    bl ox_array_new')
            self.push('i32')
            if node.repeat is not None:
                #se evalúa una sola vez el inicializador de repetición
                self.expression(node.expressions[0])
                self.convert(self.data_type(node.expressions[0]), data_type[1])
                if data_type[1] == 'f64':
                    self.emit('    fmov x1, d0')
                else:
                    self.emit('    mov x1, x0')
                self.emit('    ldr x0, [sp]', '    bl ox_array_fill')
            else:
                for index, expression in enumerate(node.expressions):
                    self.expression(expression)
                    self.convert(self.data_type(expression), data_type[1])
                    if data_type[1] == 'f64':
                        self.emit('    fmov x2, d0')
                    else:
                        self.emit('    mov x2, x0')
                    self.g.integer(index, 'x1')
                    self.emit('    ldr x0, [sp]', '    bl ox_array_set')
            self.pop('i32')
        elif kind == 'ArrayAccess':
            self.address(node)
            if not array_type(data_type):
                self.emit(f'    ldr {"d0" if data_type == "f64" else "x0"}, [x0]')
        elif kind == 'SliceAccess':
            self.call('ox_slice', [node.array, node.start, node.end], [self.data_type(node.array), 'i32', 'i32'], ('slice', self.data_type(node.array)[1], None))
        elif kind == 'Unary':
            self.expression(node.expression)
            if node.operator == '!':
                self.emit('    eor x0, x0, #1')
            elif data_type == 'f64':
                self.emit('    fneg d0, d0')
            else:
                self.emit('    neg w0, w0', '    sxtw x0, w0')
        elif kind == 'Logical':
            end = self.g.label('short')
            self.expression(node.left)
            self.emit(f'    {"cbz" if node.operator == "&&" else "cbnz"} x0, {end}')
            self.expression(node.right)
            self.emit(end + ':')
        elif kind in ('Arithmetic', 'Relational'):
            left, right = self.data_type(node.left), self.data_type(node.right)
            self.expression(node.left)
            self.push(left)
            self.expression(node.right)
            if kind == 'Arithmetic':
                self.operation(left, right, node.operator)
            else:
                self.pop(left, 'd1' if left == 'f64' else 'x1')
                self.compare(left, right, node.operator)
        elif kind == 'FunctionCall':
            params = self.semantic.parameters[node.name]
            self.call('ox_fn_' + node.name, node.arguments, [param.data_type for param in params], data_type)
        elif kind == 'NativeCall':
            self.native(node)

    def address(self, node):
        if type(node).__name__ == 'Identifier':
            self.local_address(self.semantic.bindings[id(node)])
            return
        self.expression(node.array)
        self.push('i32')
        self.expression(node.index)
        self.emit('    mov x1, x0')
        self.pop('i32')
        self.emit('    bl ox_subarray' if array_type(self.data_type(node)) else '    bl ox_index')

    #el operando izquierdo está guardado; derecho está en x0/d0
    def operation(self, left, right, operator):
        result = 'f64' if 'f64' in (left, right) else left
        if 'String' in (left, right):
            if left == 'String':
                self.emit('    mov x1, x0')
                self.pop(left)
            else:
                self.pop(left, 'x1')
            self.emit('    bl ox_concat' if operator == '+' else '    bl ox_repeat')
            return 'String'
        if result == 'f64':
            self.convert(right, 'f64')
            self.pop(left, 'd1' if left == 'f64' else 'x1')
            if left != 'f64':
                self.emit('    scvtf d1, w1')
            if operator in ('/', '%'):
                self.emit('    fcmp d0, #0.0', '    b.eq ox_zero')
            if operator == '%':
                self.emit('    fmov d2, d0', '    fmov d0, d1', '    fmov d1, d2', '    bl fmod')
            else:
                op = {'+': 'fadd', '-': 'fsub', '*': 'fmul', '/': 'fdiv'}[operator]
                self.emit(f'    {op} d0, d1, d0')
        else:
            self.pop(left, 'x1')
            if operator in ('/', '%'):
                self.emit('    cbz w0, ox_zero')
            if operator == '%':
                self.emit('    sdiv w2, w1, w0', '    msub w0, w2, w0, w1')
            else:
                op = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'sdiv'}[operator]
                self.emit(f'    {op} w0, w1, w0')
            self.emit('    sxtw x0, w0')
        return result

    def compare(self, left, right, operator):
        condition = {'==': 'eq', '!=': 'ne', '<': 'lt', '<=': 'le', '>': 'gt', '>=': 'ge'}[operator]
        if left == 'String':
            self.emit('    mov x2, x0', '    mov x0, x1', '    mov x1, x2', '    bl strcmp', '    cmp w0, #0')
        elif 'f64' in (left, right):
            self.convert(right, 'f64')
            if left != 'f64':
                self.emit('    scvtf d1, w1')
            self.emit('    fcmp d1, d0')
            condition = {'<': 'mi', '<=': 'ls'}.get(operator, condition)
        else:
            self.emit('    cmp x1, x0')
        self.emit(f'    cset x0, {condition}')

    #clasificación AAPCS64: bancos independientes y argumentos excedentes en stack
    def call(self, label, args, expected, result):
        for argument, data_type in zip(args, expected):
            self.expression(argument)
            self.convert(self.data_type(argument), data_type)
            self.push(data_type)
        locations = []
        integers = floats = stack = 0
        for data_type in expected:
            count = floats if data_type == 'f64' else integers
            if count < 8:
                locations.append(('d' if data_type == 'f64' else 'x') + str(count))
                if data_type == 'f64':
                    floats += 1
                else:
                    integers += 1
            else:
                locations.append(stack)
                stack += 1
        stack_bytes = (stack * 8 + 15) // 16 * 16
        self.g.integer(stack_bytes, 'x9')
        self.emit('    sub sp, sp, x9')
        for index, location in enumerate(locations):
            self.g.integer(stack_bytes + (len(args) - index - 1) * 16, 'x9')
            if isinstance(location, int):
                self.emit('    ldr x10, [sp, x9]')
                self.g.integer(location * 8, 'x9')
                self.emit('    str x10, [sp, x9]')
            else:
                self.emit(f'    ldr {location}, [sp, x9]')
        self.emit(f'    bl {label}')
        self.g.integer(stack_bytes + len(args) * 16, 'x9')
        self.emit('    add sp, sp, x9')

    def native(self, node):
        method = node.name
        target = self.data_type(node.target) if node.target else None
        args = node.arguments
        if method == 'typeof':
            from .types import name
            self.g.string(name(self.data_type(args[0])))
        elif method == 'String::new':
            self.g.string('')
            self.emit('    bl ox_string_copy')
        elif method == 'String::from':
            self.expression(args[0])
            if self.data_type(args[0]) == 'f64':
                self.emit('    fmov x0, d0')
            self.g.address(self.g.descriptor(self.data_type(args[0])), 'x1')
            self.emit('    bl ox_to_string')
        elif method in ('abs', 'sqrt'):
            self.expression(args[0])
            if method == 'sqrt':
                self.convert(self.data_type(args[0]), 'f64')
                self.emit('    fcmp d0, #0.0', '    b.mi ox_negative', '    fsqrt d0, d0')
            elif self.data_type(args[0]) == 'f64':
                self.emit('    fabs d0, d0')
            else:
                self.emit('    cmp w0, #0', '    cneg w0, w0, lt', '    sxtw x0, w0')
        elif method == 'clone' and not array_type(target) and target != 'String':
            self.expression(node.target)
        else:
            values = ([node.target] if node.target else []) + args
            expected = [self.data_type(value) for value in values]
            labels = {'random': 'ox_random', 'len': 'ox_length' if array_type(target) else 'ox_strlen', 'contains': ('ox_contains_float' if target[1] == 'f64' else 'ox_contains_array') if array_type(target) else 'ox_contains', 'replace': 'ox_replace', 'split': 'ox_split', 'to_uppercase': 'ox_upper', 'to_lowercase': 'ox_lower', 'reverse': 'ox_reverse', 'clone': 'ox_clone_array' if array_type(target) else 'ox_string_copy', 'chars': 'ox_chars'}
            if method == 'contains' and array_type(target):
                expected[1] = target[1]
            if method == 'contains' and target == 'String' and expected[1] == 'char':
                self.expression(node.target)
                self.push('String')
                self.expression(args[0])
                self.emit('    bl ox_char_string', '    mov x1, x0')
                self.pop('String')
                self.emit('    bl ox_contains')
            else:
                self.call(labels[method], values, expected, self.data_type(node))
