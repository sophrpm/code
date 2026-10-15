import struct
from .types import array_type, width


class Generator:
    def __init__(self):
        self.code = []
        self.data = []
        self.counter = 0
        self.descriptors = {}

    def emit(self, *lines):
        self.code.extend(lines)

    def label(self, prefix='L'):
        self.counter += 1
        return f'.L_{prefix}_{self.counter}'

    def integer(self, value, register='x0'):
        value = value & ((1 << 64) - 1)
        self.emit(f'    movz {register}, #{value & 65535}')
        for shift in (16, 32, 48):
            part = (value >> shift) & 65535
            if part:
                self.emit(f'    movk {register}, #{part}, lsl #{shift}')

    def address(self, label, register='x0'):
        self.emit(f'    adrp {register}, {label}', f'    add {register}, {register}, :lo12:{label}')

    def string(self, value):
        label = self.label('str')
        data = list(value.encode('utf-8')) + [0]
        self.data.extend([f'{label}:', '    .byte ' + ','.join(map(str, data))])
        self.address(label)

    def floating(self, value):
        self.integer(struct.unpack('<Q', struct.pack('<d', value))[0])
        self.emit('    fmov d0, x0')

    def descriptor(self, value):
        if value in self.descriptors:
            return self.descriptors[value]
        label = self.label('type')
        self.descriptors[value] = label
        kind = {'i32': 1, 'f64': 2, 'bool': 3, 'char': 4, 'String': 5, 'void': 0}
        child = self.descriptor(value[1]) if array_type(value) else '0'
        size = width(value) if not array_type(value) or value[2] is not None else 8
        length = value[2] if array_type(value) and value[2] is not None else 0
        self.data.extend(['    .balign 8', f'{label}:', f'    .quad {6 if array_type(value) else kind[value]}, {size}, {child}, {length}'])
        return label

    def finish(self):
        return '\n'.join(['// OxigenNative: AST -> AArch64', '.section .rodata'] + self.data + ['.data', '.text', '.global main', '.balign 4'] + self.code + ['.section .note.GNU-stack,"",@progbits', ''])
