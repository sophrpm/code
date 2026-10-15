# Gramática real implementada

Fuente normativa de esta lista: docstrings de producciones en `backend/analyzer/parser.py`. Incluye extensiones del intérprete que el compilador puede rechazar semánticamente; reconocer una producción no implica soportar su generación nativa.

## Tokens y palabras reservadas

```python
reserved = {'fn': 'FN', 'let': 'LET', 'mut': 'MUT', 'if': 'IF', 'else': 'ELSE', 'while': 'WHILE', 'loop': 'LOOP', 'match': 'MATCH', 'break': 'BREAK', 'continue': 'CONTINUE', 'return': 'RETURN', 'struct': 'STRUCT', 'true': 'TRUE', 'false': 'FALSE', 'i32': 'TYPE_I32', 'f64': 'TYPE_F64', 'bool': 'TYPE_BOOL', 'char': 'TYPE_CHAR', 'String': 'TYPE_STRING'}
```

```python
tokens = ['ID', 'INTEGER', 'FLOAT', 'STRING_LITERAL', 'RAW_STRING', 'CHAR_LITERAL', 'LABEL', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO', 'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN', 'DIVIDE_ASSIGN', 'MODULO_ASSIGN', 'EQUAL', 'NOT_EQUAL', 'GREATER', 'GREATER_EQUAL', 'LESS', 'LESS_EQUAL', 'NOT', 'AND', 'OR', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET', 'SEMICOLON', 'COLON', 'COMMA', 'DOT', 'DOUBLE_COLON', 'ARROW', 'FAT_ARROW', 'RANGE', 'AMPERSAND', 'PRINTLN'] + list(reserved.values())
```

Identificadores ASCII: `[a-zA-Z_][a-zA-Z0-9_]*`. Enteros decimales; f64 con parte entera y decimal. Comentarios // y /* ... */. Literales char y String con escapes; raw strings r"..." y r#"..."#. No se reconocen exponentes, bases numéricas ni comentarios anidados.

## Precedencia

```python
precedence = (('left', 'OR'), ('left', 'AND'), ('nonassoc', 'EQUAL', 'NOT_EQUAL', 'GREATER', 'GREATER_EQUAL', 'LESS', 'LESS_EQUAL'), ('left', 'PLUS', 'MINUS'), ('left', 'TIMES', 'DIVIDE', 'MODULO'), ('right', 'NOT', 'UMINUS'))
```

## Producciones PLY

```text
program : global_list

global_list : global_list global_instruction

global_list : global_instruction

global_list : empty

global_instruction : function_declaration
                   | struct_declaration

type_spec : TYPE_I32

type_spec : TYPE_F64

type_spec : TYPE_BOOL

type_spec : TYPE_CHAR

type_spec : TYPE_STRING

type_spec : ID

type_spec : LBRACKET type_spec SEMICOLON INTEGER RBRACKET

function_declaration : FN ID LPAREN parameter_list_opt RPAREN return_type_opt block

parameter_list_opt : parameter_list
                   | empty

parameter_list : parameter

parameter_list : parameter_list COMMA parameter

parameter : ID COLON type_spec

return_type_opt : ARROW type_spec

return_type_opt : empty

struct_declaration : STRUCT ID LBRACE struct_field_list_opt RBRACE

struct_field_list_opt : struct_field_list
                      | empty

struct_field_list : struct_field

struct_field_list : struct_field_list COMMA struct_field

struct_field_list : struct_field_list COMMA

struct_field : ID COLON type_spec

block : LBRACE statement_list RBRACE

statement_list : statement_list statement

statement_list : empty

statement : simple_statement SEMICOLON

statement : control_statement

statement : block

statement : error SEMICOLON

simple_statement : declaration
                 | assignment
                 | print_instruction
                 | break_instruction
                 | continue_instruction
                 | return_instruction
                 | expression_instruction

control_statement : if_instruction
                  | while_instruction
                  | loop_instruction
                  | match_instruction

let_prefix : LET

let_prefix : LET MUT

declaration : let_prefix ID

declaration : let_prefix ID COLON type_spec

declaration : let_prefix ID ASSIGN value_expression

declaration : let_prefix ID COLON type_spec ASSIGN value_expression

declaration : let_prefix ID ASSIGN slice_expression

array_values : LBRACKET value_expression_list RBRACKET

array_repeat : LBRACKET value_expression SEMICOLON INTEGER RBRACKET

value_expression_list : value_expression

value_expression_list : value_expression_list COMMA value_expression

value_expression_list : value_expression_list COMMA

primary : array_values

primary : array_repeat

array_values : LBRACKET RBRACKET

slice_expression : AMPERSAND postfix LBRACKET expression RANGE expression RBRACKET

assignment : postfix assignment_operator value_expression

assignment_operator : ASSIGN
                    | PLUS_ASSIGN
                    | MINUS_ASSIGN
                    | TIMES_ASSIGN
                    | DIVIDE_ASSIGN
                    | MODULO_ASSIGN

print_instruction : PRINTLN LPAREN print_arguments_opt RPAREN

print_arguments_opt : value_expression_list
                    | empty

if_instruction : IF expression block else_part

else_part : ELSE block

else_part : ELSE IF expression block else_part

else_part : empty

while_instruction : WHILE expression block

loop_instruction : LOOP block

loop_instruction : LABEL COLON LOOP block

match_instruction : MATCH expression LBRACE match_arm_list RBRACE

match_arm_list : match_arm

match_arm_list : match_arm_list match_arm

match_arm : expression FAT_ARROW match_body COMMA

match_body : simple_statement

match_body : control_statement

match_body : block

break_instruction : BREAK

break_instruction : BREAK LABEL

continue_instruction : CONTINUE

continue_instruction : CONTINUE LABEL

return_instruction : RETURN

return_instruction : RETURN value_expression

expression_instruction : value_expression

struct_instance : ID LBRACE struct_value_list_opt RBRACE

struct_value_list_opt : struct_value_list
                      | empty

struct_value_list : struct_value

struct_value_list : struct_value_list COMMA struct_value

struct_value_list : struct_value_list COMMA

struct_value : ID COLON value_expression

value_expression : expression

value_expression : struct_instance

expression : expression PLUS expression
           | expression MINUS expression
           | expression TIMES expression
           | expression DIVIDE expression
           | expression MODULO expression

expression : expression EQUAL expression
           | expression NOT_EQUAL expression
           | expression GREATER expression
           | expression GREATER_EQUAL expression
           | expression LESS expression
           | expression LESS_EQUAL expression

expression : expression AND expression
           | expression OR expression

expression : MINUS expression %prec UMINUS

expression : NOT expression

expression : postfix

postfix : primary

postfix : postfix LBRACKET expression RBRACKET

postfix : postfix DOT member

member : ID

member : ID LPAREN argument_list_opt RPAREN

primary : INTEGER

primary : FLOAT

primary : TRUE

primary : FALSE

primary : STRING_LITERAL

primary : RAW_STRING

primary : CHAR_LITERAL

primary : ID

primary : LPAREN expression RPAREN

primary : ID LPAREN argument_list_opt RPAREN

primary : TYPE_STRING DOUBLE_COLON ID LPAREN argument_list_opt RPAREN

argument_list_opt : argument_list
                  | empty

argument_list : value_expression

argument_list : argument_list COMMA value_expression

argument_list : argument_list COMMA

empty :

```

## Cambios respecto del Proyecto 1

Los arreglos literales y por repetición ahora son primarios, lo que permite anidarlos, pasarlos como argumentos y retornarlos. Se reconoce el arreglo vacío para contextos tipados de longitud cero. Los tipos anidados conservan `nested_type` en vez de descartar dimensiones. Los parámetros conservan `type_info` y los retornos `return_info`. Se mantiene el AST compartido, los tokens y la precedencia originales.

Las declaraciones sin expresión de i32, f64, bool y String son transformadas por el parser en literales de valor por defecto. Char y arreglos no tienen ese valor en modo nativo. Las funciones globales y main son obligatorias; no se permiten instrucciones sueltas globales. `match` requiere un comodín final y coma después de cada brazo.
