# analyzer/parser.py

import ply.yacc as yacc

from .lexer import tokens
from .lexer import lexer
from .lexer import error_manager as lexical_error_manager

from ..errors.error_manager import ErrorManager

from ..interpreter.types import Types
from ..interpreter.result import Result

from ..ast.node import Node

from ..ast.expressions.literal import Literal
from ..ast.expressions.identifier import Identifier
from ..ast.expressions.arithmetic import Arithmetic
from ..ast.expressions.relational import Relational
from ..ast.expressions.logical import Logical
from ..ast.expressions.unary import Unary
from ..ast.expressions.array_access import ArrayAccess
from ..ast.expressions.slice_access import SliceAccess
from ..ast.expressions.struct_access import StructAccess
from ..ast.expressions.function_call import FunctionCall
from ..ast.expressions.native_call import NativeCall

from ..ast.expressions.struct_instance import StructInstance
from ..ast.instructions.declaration import Declaration
from ..ast.instructions.assignment import Assignment
from ..ast.instructions.print_instruction import PrintInstruction
from ..ast.instructions.if_instruction import IfInstruction
from ..ast.instructions.while_instruction import WhileInstruction
from ..ast.instructions.loop_instruction import LoopInstruction
from ..ast.instructions.match_instruction import MatchInstruction
from ..ast.instructions.break_instruction import BreakInstruction
from ..ast.instructions.continue_instruction import ContinueInstruction
from ..ast.instructions.return_instruction import ReturnInstruction
from ..ast.instructions.array_declaration import ArrayDeclaration
from ..ast.instructions.slice_declaration import SliceDeclaration
from ..ast.instructions.struct_declaration import StructDeclaration
from ..ast.instructions.function_declaration import FunctionDeclaration
from ..ast.instructions.main_function import MainFunction
from ..ast.instructions.block_instruction import BlockInstruction


#Errores sintacticos

error_manager = ErrorManager()

source_code = ""


#Nativas globales

global_natives = {
    "typeof",
    "random",
    "abs",
    "sqrt",
}


#Metodos nativos

native_methods = {
    "len",
    "contains",
    "replace",
    "split",
    "to_uppercase",
    "to_lowercase",
    "reverse",
    "clone",
    "chars",
    "push",
    "remove",
}


#Precedencia

precedence = (

    ("left", "OR"),

    ("left", "AND"),

    ("nonassoc", "EQUAL", "NOT_EQUAL", "GREATER", "GREATER_EQUAL", "LESS", "LESS_EQUAL"),

    ("left", "PLUS", "MINUS"),

    ("left", "TIMES", "DIVIDE", "MODULO"),

    ("right", "NOT", "UMINUS"),
)


start = "program"


#Permite ejecutar una expresion como instruccion

class ExpressionInstruction(Node):

    def __init__(self, expression, line, column):
        super().__init__(line, column)

        self.expression = expression


    def execute(self, environment):

        self.expression.evaluate(environment)

        return Result.normal()


#Obtiene columna

def get_column(position):

    if position is None:
        return 0

    last_line = source_code.rfind("\n", 0, position)

    return position - last_line


#Obtiene fragmento de linea

def get_fragment(line):

    if line <= 0:
        return ""

    lines = source_code.splitlines()

    if line > len(lines):
        return ""

    return lines[line - 1]


#Registra error sintactico

def add_syntax_error(description, line, column):

    fragment = get_fragment(line)

    error_manager.syntactic(description, line, column, fragment)


#Procesa escapes

def decode_string(value):

    result = ""
    index = 0

    escapes = {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "\\": "\\",
        "\"": "\"",
        "'": "'",
    }


    while index < len(value):

        current = value[index]


        if current == "\\" and index + 1 < len(value):

            next_char = value[index + 1]


            if next_char in escapes:

                result += escapes[next_char]
                index += 2
                continue


        result += current
        index += 1


    return result


#Crea informacion de tipo

def make_type(data_type, element_type=None, size=None):

    return {
        "data_type": data_type,
        "element_type": element_type,
        "size": size,
    }


#Crea valor por defecto

def default_value(type_info, line, column):

    data_type = type_info["data_type"]


    if data_type == Types.I32:
        return Literal(0, Types.I32, line, column)


    if data_type == Types.F64:
        return Literal(0.0, Types.F64, line, column)


    if data_type == Types.BOOL:
        return Literal(False, Types.BOOL, line, column)


    if data_type == Types.STRING:
        return Literal("", Types.STRING, line, column)


    return None


#Crea println

def build_print(values, line, column):

    if len(values) == 0:

        text = Literal("", Types.STRING, line, column)

        return PrintInstruction(text, [], line, column)


    first = values[0]


    #println!("texto")
    if len(values) == 1 and isinstance(first, Literal) and first.data_type == Types.STRING:

        first.value = first.value.replace("{:?}", "{}")

        return PrintInstruction(first, [], line, column)


    #println!(variable)
    if len(values) == 1:

        text = Literal("{}", Types.STRING, line, column)

        return PrintInstruction(text, [first], line, column)


    #println!("{}", valor)
    if isinstance(first, Literal) and first.data_type == Types.STRING:
        first.value = first.value.replace("{:?}", "{}")


    return PrintInstruction(first, values[1:], line, column)


#PROGRAMA


def p_program(p):
    """
    program : global_list
    """

    p[0] = p[1]


def p_global_list_multiple(p):
    """
    global_list : global_list global_instruction
    """

    p[0] = p[1]

    if p[2] is not None:
        p[0].append(p[2])


def p_global_list_single(p):
    """
    global_list : global_instruction
    """

    if p[1] is None:
        p[0] = []
    else:
        p[0] = [p[1]]


def p_global_list_empty(p):
    """
    global_list : empty
    """

    p[0] = []


def p_global_instruction(p):
    """
    global_instruction : function_declaration
                       | struct_declaration
    """

    p[0] = p[1]


#TIPOS


def p_type_i32(p):
    """
    type_spec : TYPE_I32
    """

    p[0] = make_type(Types.I32)


def p_type_f64(p):
    """
    type_spec : TYPE_F64
    """

    p[0] = make_type(Types.F64)


def p_type_bool(p):
    """
    type_spec : TYPE_BOOL
    """

    p[0] = make_type(Types.BOOL)


def p_type_char(p):
    """
    type_spec : TYPE_CHAR
    """

    p[0] = make_type(Types.CHAR)


def p_type_string(p):
    """
    type_spec : TYPE_STRING
    """

    p[0] = make_type(Types.STRING)


def p_type_struct(p):
    """
    type_spec : ID
    """

    #Nombre de un struct
    p[0] = make_type(p[1])


def p_type_array(p):
    """
    type_spec : LBRACKET type_spec SEMICOLON INTEGER RBRACKET
    """

    p[0] = make_type(Types.ARRAY, p[2]["data_type"], p[4])


#FUNCIONES


def p_function_declaration(p):
    """
    function_declaration : FN ID LPAREN parameter_list_opt RPAREN return_type_opt block
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    name = p[2]
    parameters = p[4]
    return_type = p[6]
    instructions = p[7]["instructions"]


    #Funcion main
    if name == "main":

        if len(parameters) != 0:

            add_syntax_error("La funcion main no puede recibir parametros", line, column)


        if return_type != Types.VOID:

            add_syntax_error("La funcion main no debe declarar tipo de retorno", line, column)


        p[0] = MainFunction(instructions, line, column)
        return


    p[0] = FunctionDeclaration(name, parameters, return_type, instructions, line, column)


def p_parameter_list_opt(p):
    """
    parameter_list_opt : parameter_list
                       | empty
    """

    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]


def p_parameter_list_single(p):
    """
    parameter_list : parameter
    """

    p[0] = [p[1]]


def p_parameter_list_multiple(p):
    """
    parameter_list : parameter_list COMMA parameter
    """

    p[0] = p[1]
    p[0].append(p[3])


def p_parameter(p):
    """
    parameter : ID COLON type_spec
    """

    p[0] = {
        "name": p[1],
        "data_type": p[3]["data_type"],
        "element_type": p[3]["element_type"],
        "size": p[3]["size"],
    }


def p_return_type(p):
    """
    return_type_opt : ARROW type_spec
    """

    p[0] = p[2]["data_type"]


def p_return_type_empty(p):
    """
    return_type_opt : empty
    """

    p[0] = Types.VOID


#STRUCTS


def p_struct_declaration(p):
    """
    struct_declaration : STRUCT ID LBRACE struct_field_list_opt RBRACE
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    p[0] = StructDeclaration(p[2], p[4], line, column)


def p_struct_field_list_opt(p):
    """
    struct_field_list_opt : struct_field_list
                          | empty
    """

    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]


def p_struct_field_list_single(p):
    """
    struct_field_list : struct_field
    """

    p[0] = [p[1]]


def p_struct_field_list_multiple(p):
    """
    struct_field_list : struct_field_list COMMA struct_field
    """

    p[0] = p[1]
    p[0].append(p[3])


def p_struct_field_list_trailing(p):
    """
    struct_field_list : struct_field_list COMMA
    """

    p[0] = p[1]


def p_struct_field(p):
    """
    struct_field : ID COLON type_spec
    """

    p[0] = {
        "name": p[1],
        "data_type": p[3]["data_type"],
    }


#BLOQUES


def p_block(p):
    """
    block : LBRACE statement_list RBRACE
    """

    p[0] = {
        "instructions": p[2],
        "line": p.lineno(1),
        "column": get_column(p.lexpos(1)),
    }


def p_statement_list_multiple(p):
    """
    statement_list : statement_list statement
    """

    p[0] = p[1]

    if p[2] is not None:
        p[0].append(p[2])


def p_statement_list_empty(p):
    """
    statement_list : empty
    """

    p[0] = []


#INSTRUCCIONES


def p_statement_simple(p):
    """
    statement : simple_statement SEMICOLON
    """

    p[0] = p[1]


def p_statement_control(p):
    """
    statement : control_statement
    """

    p[0] = p[1]


def p_statement_block(p):
    """
    statement : block
    """

    block = p[1]
    p[0] = BlockInstruction(block["instructions"], block["line"], block["column"])


def p_statement_error(p):
    """
    statement : error SEMICOLON
    """

    p[0] = None


def p_simple_statement(p):
    """
    simple_statement : declaration
                     | assignment
                     | print_instruction
                     | break_instruction
                     | continue_instruction
                     | return_instruction
                     | expression_instruction
    """

    p[0] = p[1]


def p_control_statement(p):
    """
    control_statement : if_instruction
                      | while_instruction
                      | loop_instruction
                      | match_instruction
    """

    p[0] = p[1]


#DECLARACIONES


def p_let_prefix_normal(p):
    """
    let_prefix : LET
    """

    p[0] = {
        "mutable": False,
        "line": p.lineno(1),
        "column": get_column(p.lexpos(1)),
    }


def p_let_prefix_mutable(p):
    """
    let_prefix : LET MUT
    """

    p[0] = {
        "mutable": True,
        "line": p.lineno(1),
        "column": get_column(p.lexpos(1)),
    }


#let x

def p_declaration_empty(p):
    """
    declaration : let_prefix ID
    """

    info = p[1]

    p[0] = Declaration(p[2], None, None, info["mutable"], info["line"], info["column"])


#let x: tipo

def p_declaration_type(p):
    """
    declaration : let_prefix ID COLON type_spec
    """

    info = p[1]
    type_info = p[4]

    expression = default_value(type_info, info["line"], info["column"])


    p[0] = Declaration(p[2], expression, type_info["data_type"], info["mutable"], info["line"], info["column"])


#let x = expresion

def p_declaration_expression(p):
    """
    declaration : let_prefix ID ASSIGN value_expression
    """

    info = p[1]

    p[0] = Declaration(p[2], p[4], None, info["mutable"], info["line"], info["column"])


#let x: tipo = expresion

def p_declaration_typed_expression(p):
    """
    declaration : let_prefix ID COLON type_spec ASSIGN value_expression
    """

    info = p[1]
    type_info = p[4]


    p[0] = Declaration(p[2], p[6], type_info["data_type"], info["mutable"], info["line"], info["column"])


#let x = [1, 2, 3]

def p_declaration_array_values(p):
    """
    declaration : let_prefix ID ASSIGN array_values
    """

    info = p[1]
    values = p[4]


    p[0] = ArrayDeclaration(p[2], values, None, len(values), info["mutable"], info["line"], info["column"], False)


#let x: [i32; 3] = [1, 2, 3]

def p_declaration_typed_array(p):
    """
    declaration : let_prefix ID COLON type_spec ASSIGN array_values
    """

    info = p[1]
    type_info = p[4]


    if type_info["data_type"] != Types.ARRAY:

        add_syntax_error("El tipo de una declaracion de arreglo debe tener la forma [tipo; tamanio]", info["line"], info["column"])


    p[0] = ArrayDeclaration(p[2], p[6], type_info["element_type"], type_info["size"], info["mutable"], info["line"], info["column"], False)


#let x = [valor; cantidad]

def p_declaration_array_repeat(p):
    """
    declaration : let_prefix ID ASSIGN array_repeat
    """

    info = p[1]
    repeat = p[4]


    p[0] = ArrayDeclaration(p[2], [repeat["expression"]], None, repeat["size"], info["mutable"], info["line"], info["column"], True)


#let parte = &numeros[1..4]

def p_declaration_slice(p):
    """
    declaration : let_prefix ID ASSIGN slice_expression
    """

    info = p[1]


    p[0] = SliceDeclaration(p[2], p[4], info["mutable"], info["line"], info["column"])


#ARRAYS


def p_array_values(p):
    """
    array_values : LBRACKET value_expression_list RBRACKET
    """

    p[0] = p[2]


def p_array_repeat(p):
    """
    array_repeat : LBRACKET value_expression SEMICOLON INTEGER RBRACKET
    """

    p[0] = {
        "expression": p[2],
        "size": p[4],
    }


def p_value_expression_list_single(p):
    """
    value_expression_list : value_expression
    """

    p[0] = [p[1]]


def p_value_expression_list_multiple(p):
    """
    value_expression_list : value_expression_list COMMA value_expression
    """

    p[0] = p[1]
    p[0].append(p[3])


def p_value_expression_list_trailing(p):
    """
    value_expression_list : value_expression_list COMMA
    """

    p[0] = p[1]


#SLICE


def p_slice_expression(p):
    """
    slice_expression : AMPERSAND postfix LBRACKET expression RANGE expression RBRACKET
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = SliceAccess(p[2], p[4], p[6], line, column)


#ASIGNACIONES


def p_assignment(p):
    """
    assignment : postfix assignment_operator value_expression
    """

    line = p[1].line
    column = p[1].column


    if not isinstance(p[1], (Identifier, ArrayAccess, StructAccess)):

        add_syntax_error("El lado izquierdo de una asignacion no es valido", line, column)


    p[0] = Assignment(p[1], p[2], p[3], line, column)


def p_assignment_operator(p):
    """
    assignment_operator : ASSIGN
                        | PLUS_ASSIGN
                        | MINUS_ASSIGN
                        | TIMES_ASSIGN
                        | DIVIDE_ASSIGN
                        | MODULO_ASSIGN
    """

    p[0] = p[1]


#PRINTLN


def p_print_instruction(p):
    """
    print_instruction : PRINTLN LPAREN print_arguments_opt RPAREN
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    p[0] = build_print(p[3], line, column)


def p_print_arguments_opt(p):
    """
    print_arguments_opt : value_expression_list
                        | empty
    """

    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]


#IF


def p_if_instruction(p):
    """
    if_instruction : IF expression block else_part
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = IfInstruction(p[2], p[3]["instructions"], p[4], line, column)


def p_else_part_block(p):
    """
    else_part : ELSE block
    """

    p[0] = p[2]["instructions"]


def p_else_part_if(p):
    """
    else_part : ELSE IF expression block else_part
    """

    line = p.lineno(2)
    column = get_column(p.lexpos(2))


    nested_if = IfInstruction(p[3], p[4]["instructions"], p[5], line, column)


    p[0] = [nested_if]


def p_else_part_empty(p):
    """
    else_part : empty
    """

    p[0] = []


#WHILE


def p_while_instruction(p):
    """
    while_instruction : WHILE expression block
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = WhileInstruction(p[2], p[3]["instructions"], line, column)


#LOOP


def p_loop_instruction(p):
    """
    loop_instruction : LOOP block
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = LoopInstruction(p[2]["instructions"], line, column)


def p_loop_instruction_label(p):
    """
    loop_instruction : LABEL COLON LOOP block
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = LoopInstruction(p[4]["instructions"], line, column, p[1])


#MATCH


def p_match_instruction(p):
    """
    match_instruction : MATCH expression LBRACE match_arm_list RBRACE
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    arms = p[4]

    wildcard_count = 0
    wildcard_index = -1


    for index in range(len(arms)):

        if arms[index]["default"]:
            wildcard_count += 1
            wildcard_index = index


    if wildcard_count == 0:

        add_syntax_error("La sentencia match debe incluir el caso comodin _", line, column)


    if wildcard_count > 1:

        add_syntax_error("La sentencia match solo puede tener un caso comodin _", line, column)


    if wildcard_index != -1 and wildcard_index != len(arms) - 1:

        add_syntax_error("El caso comodin _ debe ser el ultimo caso del match", line, column)


    p[0] = MatchInstruction(p[2], arms, line, column)


def p_match_arm_list_single(p):
    """
    match_arm_list : match_arm
    """

    p[0] = [p[1]]


def p_match_arm_list_multiple(p):
    """
    match_arm_list : match_arm_list match_arm
    """

    p[0] = p[1]
    p[0].append(p[2])


def p_match_arm(p):
    """
    match_arm : expression FAT_ARROW match_body COMMA
    """

    pattern = p[1]

    is_default = False


    if isinstance(pattern, Identifier) and pattern.name == "_":

        is_default = True
        pattern = None


    p[0] = {
        "pattern": pattern,
        "instruction": p[3],
        "default": is_default,
    }


def p_match_body_simple(p):
    """
    match_body : simple_statement
    """

    p[0] = p[1]


def p_match_body_control(p):
    """
    match_body : control_statement
    """

    p[0] = p[1]


def p_match_body_block(p):
    """
    match_body : block
    """

    block = p[1]
    p[0] = BlockInstruction(block["instructions"], block["line"], block["column"])


#BREAK


def p_break_instruction(p):
    """
    break_instruction : BREAK
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = BreakInstruction(None, line, column)


def p_break_instruction_label(p):
    """
    break_instruction : BREAK LABEL
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = BreakInstruction(p[2], line, column)


#CONTINUE


def p_continue_instruction(p):
    """
    continue_instruction : CONTINUE
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = ContinueInstruction(None, line, column)


def p_continue_instruction_label(p):
    """
    continue_instruction : CONTINUE LABEL
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = ContinueInstruction(p[2], line, column)


#RETURN


def p_return_instruction_empty(p):
    """
    return_instruction : RETURN
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = ReturnInstruction(None, line, column)


def p_return_instruction_value(p):
    """
    return_instruction : RETURN value_expression
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = ReturnInstruction(p[2], line, column)


#EXPRESION COMO INSTRUCCION


def p_expression_instruction(p):
    """
    expression_instruction : value_expression
    """

    expression = p[1]


    p[0] = ExpressionInstruction(expression, expression.line, expression.column)


#STRUCT INSTANCE


def p_struct_instance(p):
    """
    struct_instance : ID LBRACE struct_value_list_opt RBRACE
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = StructInstance(p[1], p[3], line, column)


def p_struct_value_list_opt(p):
    """
    struct_value_list_opt : struct_value_list
                          | empty
    """

    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]


def p_struct_value_list_single(p):
    """
    struct_value_list : struct_value
    """

    p[0] = [p[1]]


def p_struct_value_list_multiple(p):
    """
    struct_value_list : struct_value_list COMMA struct_value
    """

    p[0] = p[1]
    p[0].append(p[3])


def p_struct_value_list_trailing(p):
    """
    struct_value_list : struct_value_list COMMA
    """

    p[0] = p[1]


def p_struct_value(p):
    """
    struct_value : ID COLON value_expression
    """

    p[0] = {
        "name": p[1],
        "expression": p[3],
    }


#VALUE EXPRESSION


def p_value_expression_normal(p):
    """
    value_expression : expression
    """

    p[0] = p[1]


def p_value_expression_struct(p):
    """
    value_expression : struct_instance
    """

    p[0] = p[1]


#EXPRESIONES BINARIAS


def p_expression_arithmetic(p):
    """
    expression : expression PLUS expression
               | expression MINUS expression
               | expression TIMES expression
               | expression DIVIDE expression
               | expression MODULO expression
    """

    line = p[1].line
    column = p[1].column


    p[0] = Arithmetic(p[1], p[2], p[3], line, column)


def p_expression_relational(p):
    """
    expression : expression EQUAL expression
               | expression NOT_EQUAL expression
               | expression GREATER expression
               | expression GREATER_EQUAL expression
               | expression LESS expression
               | expression LESS_EQUAL expression
    """

    line = p[1].line
    column = p[1].column


    p[0] = Relational(p[1], p[2], p[3], line, column)


def p_expression_logical(p):
    """
    expression : expression AND expression
               | expression OR expression
    """

    line = p[1].line
    column = p[1].column


    p[0] = Logical(p[1], p[2], p[3], line, column)


#EXPRESIONES UNARIAS


def p_expression_negative(p):
    """
    expression : MINUS expression %prec UMINUS
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = Unary(p[1], p[2], line, column)


def p_expression_not(p):
    """
    expression : NOT expression
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))


    p[0] = Unary(p[1], p[2], line, column)


#POSTFIX


def p_expression_postfix(p):
    """
    expression : postfix
    """

    p[0] = p[1]


def p_postfix_primary(p):
    """
    postfix : primary
    """

    p[0] = p[1]


#arreglo[indice]

def p_postfix_array(p):
    """
    postfix : postfix LBRACKET expression RBRACKET
    """

    p[0] = ArrayAccess(p[1], p[3], p[1].line, p[1].column)


#objeto.campo
#objeto.metodo(...)

def p_postfix_member(p):
    """
    postfix : postfix DOT member
    """

    member = p[3]


    if member["method"]:

        if member["name"] not in native_methods:

            add_syntax_error(f"Metodo '{member['name']}' no reconocido", member["line"], member["column"])


        p[0] = NativeCall(member["name"], member["arguments"], member["line"], member["column"], p[1])

        return


    p[0] = StructAccess(p[1], member["name"], p[1].line, p[1].column)


def p_member_field(p):
    """
    member : ID
    """

    p[0] = {
        "name": p[1],
        "arguments": [],
        "method": False,
        "line": p.lineno(1),
        "column": get_column(p.lexpos(1)),
    }


def p_member_method(p):
    """
    member : ID LPAREN argument_list_opt RPAREN
    """

    p[0] = {
        "name": p[1],
        "arguments": p[3],
        "method": True,
        "line": p.lineno(1),
        "column": get_column(p.lexpos(1)),
    }


#PRIMARIOS


def p_primary_integer(p):
    """
    primary : INTEGER
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    p[0] = Literal(p[1], Types.I32, line, column)


def p_primary_float(p):
    """
    primary : FLOAT
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    p[0] = Literal(p[1], Types.F64, line, column)


def p_primary_true(p):
    """
    primary : TRUE
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    p[0] = Literal(True, Types.BOOL, line, column)


def p_primary_false(p):
    """
    primary : FALSE
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    p[0] = Literal(False, Types.BOOL, line, column)


def p_primary_string(p):
    """
    primary : STRING_LITERAL
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    value = decode_string(p[1])

    p[0] = Literal(value, Types.STRING, line, column)


def p_primary_raw_string(p):
    """
    primary : RAW_STRING
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    p[0] = Literal(p[1], Types.STRING, line, column)


def p_primary_char(p):
    """
    primary : CHAR_LITERAL
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    value = decode_string(p[1])

    p[0] = Literal(value, Types.CHAR, line, column)


def p_primary_identifier(p):
    """
    primary : ID
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    p[0] = Identifier(p[1], line, column)


def p_primary_parentheses(p):
    """
    primary : LPAREN expression RPAREN
    """

    p[0] = p[2]


#LLAMADAS A FUNCIONES


def p_primary_function_call(p):
    """
    primary : ID LPAREN argument_list_opt RPAREN
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    name = p[1]
    arguments = p[3]


    if name in global_natives:

        p[0] = NativeCall(name, arguments, line, column)

        return


    p[0] = FunctionCall(name, arguments, line, column)


#String::from(...)
#String::new()

def p_primary_string_native(p):
    """
    primary : TYPE_STRING DOUBLE_COLON ID LPAREN argument_list_opt RPAREN
    """

    line = p.lineno(1)
    column = get_column(p.lexpos(1))

    name = p[3]


    if name != "from" and name != "new":

        add_syntax_error(f"Funcion String::{name} no reconocida", line, column)


    p[0] = NativeCall(f"String::{name}", p[5], line, column)


#ARGUMENTOS


def p_argument_list_opt(p):
    """
    argument_list_opt : argument_list
                      | empty
    """

    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]


def p_argument_list_single(p):
    """
    argument_list : value_expression
    """

    p[0] = [p[1]]


def p_argument_list_multiple(p):
    """
    argument_list : argument_list COMMA value_expression
    """

    p[0] = p[1]
    p[0].append(p[3])


def p_argument_list_trailing(p):
    """
    argument_list : argument_list COMMA
    """

    p[0] = p[1]


#VACIO


def p_empty(p):
    """
    empty :
    """

    p[0] = None


#ERRORES


def p_error(p):

    if p is None:

        lines = source_code.splitlines()

        line = len(lines)

        if line == 0:
            line = 1

        column = 1


        add_syntax_error("Fin de archivo inesperado", line, column)

        return


    line = p.lineno
    column = get_column(p.lexpos)


    add_syntax_error(f"Token inesperado '{p.value}'", line, column)


#CREA PARSER
parser = yacc.yacc(start=start, debug=False, write_tables=False)


#ANALIZA CODIGO
def parse(text):

    global source_code
    source_code = text
    error_manager.clear()
    lexical_error_manager.clear()
    lexer.lineno = 1
    result = parser.parse(text, lexer=lexer,tracking=True)

    if result is None:
        return []

    return result


#DEVUELVE ERRORES SINTACTICO
def get_syntactic_errors():

    return error_manager.get_errors()


#DEVUELVE TODOS LOS ERRORES DE ANALISIS
def get_analysis_errors():

    errors = []

    errors.extend(lexical_error_manager.get_errors())
    errors.extend(error_manager.get_errors())

    return errors


#VERIFICA ERRORES
def has_errors():

    if lexical_error_manager.has_errors():
        return True

    return error_manager.has_errors()

