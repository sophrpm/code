import ply.lex as lex

from ..errors.error_manager import ErrorManager


#reservedWords
reserved = {
    "fn": "FN",
    "let": "LET",
    "mut": "MUT",

    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "loop": "LOOP",
    "match": "MATCH",

    "break": "BREAK",
    "continue": "CONTINUE",
    "return": "RETURN",

    "struct": "STRUCT",

    "true": "TRUE",
    "false": "FALSE",

    "i32": "TYPE_I32",
    "f64": "TYPE_F64",
    "bool": "TYPE_BOOL",
    "char": "TYPE_CHAR",
    "String": "TYPE_STRING",
}


#tokens
tokens = [

    #Identificadores y literales
    "ID",
    "INTEGER",
    "FLOAT",
    "STRING_LITERAL",
    "RAW_STRING",
    "CHAR_LITERAL",
    "LABEL",

    #Operadores aritmeticos
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "MODULO",

    #Asignacion
    "ASSIGN",
    "PLUS_ASSIGN",
    "MINUS_ASSIGN",
    "TIMES_ASSIGN",
    "DIVIDE_ASSIGN",
    "MODULO_ASSIGN",

    #Relacionales
    "EQUAL",
    "NOT_EQUAL",
    "GREATER",
    "GREATER_EQUAL",
    "LESS",
    "LESS_EQUAL",

    #Logicos
    "NOT",
    "AND",
    "OR",

    #Simbolos especiales
    "LPAREN",
    "RPAREN",
    "LBRACE",
    "RBRACE",
    "LBRACKET",
    "RBRACKET",

    "SEMICOLON",
    "COLON",
    "COMMA",
    "DOT",

    #Rust-like
    "DOUBLE_COLON",
    "ARROW",
    "FAT_ARROW",
    "RANGE",
    "AMPERSAND",

    #println!
    "PRINTLN",

] + list(reserved.values())


#ErrorManager
error_manager = ErrorManager()


#Tokens especiales
def t_PRINTLN(t):
    r'println!'
    return t


#Raw String r#"texto"#

def t_RAW_STRING_HASH(t):
    r'r\#"([^"\n]|"(?=[^#]))*"\#'
    t.type = "RAW_STRING"
    t.value = t.value[3:-2]
    return t


#Raw String r"texto"
def t_RAW_STRING_SIMPLE(t):
    r'r"[^"\n]*"'
    t.type = "RAW_STRING"
    t.value = t.value[2:-1]
    return t


#String normal
def t_STRING_LITERAL(t):
    r'"([^"\\\n]|\\.)*"'
    t.value = t.value[1:-1]
    return t


#caracter
def t_CHAR_LITERAL(t):
    r"'([^\\'\n]|\\.)'"
    t.value = t.value[1:-1]
    return t


#etiqueta
def t_LABEL(t):
    r"'[a-zA-Z_][a-zA-Z0-9_]*"
    t.value = t.value[1:]
    return t


#comentarios
def t_BLOCK_COMMENT(t):
    r'/\*[\s\S]*?\*/'
    t.lexer.lineno += t.value.count("\n")


#Comentario de bloque sin cerrar
def t_UNCLOSED_BLOCK_COMMENT(t):
    r'/\*[\s\S]*'
    column = find_column(t.lexer.lexdata, t)
    fragment = get_line_fragment(t.lexer.lexdata, t.lineno)
    error_manager.lexical("Comentario de bloque sin cerrar", t.lineno, column, fragment)
    t.lexer.lineno += t.value.count("\n")


def t_LINE_COMMENT(t):
    r'//[^\n]*'
    pass


#numeros
def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t


def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t


#ID
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, "ID")

    return t


#Operadores compuestos
t_PLUS_ASSIGN = r'\+='
t_MINUS_ASSIGN = r'-='
t_TIMES_ASSIGN = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_MODULO_ASSIGN = r'%='

t_EQUAL = r'=='
t_NOT_EQUAL = r'!='

t_GREATER_EQUAL = r'>='
t_LESS_EQUAL = r'<='

t_AND = r'&&'
t_OR = r'\|\|'

t_DOUBLE_COLON = r'::'

t_ARROW = r'->'
t_FAT_ARROW = r'=>'

t_RANGE = r'\.\.'


#Operadores
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MODULO = r'%'

t_ASSIGN = r'='

t_GREATER = r'>'
t_LESS = r'<'

t_NOT = r'!'

t_AMPERSAND = r'&'


#Signos de agrupacion
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_LBRACE = r'\{'
t_RBRACE = r'\}'

t_LBRACKET = r'\['
t_RBRACKET = r'\]'


#Separadores
t_SEMICOLON = r';'
t_COLON = r':'
t_COMMA = r','
t_DOT = r'\.'


#ignorar espacios
t_ignore = " \t\r"


#saltos de linea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


#columna
def find_column(text, token):
    last_line = text.rfind("\n", 0, token.lexpos)
    if last_line < 0:
        last_line = -1

    return token.lexpos - last_line


#linea del codigo
def get_line_fragment(text, line):
    lines = text.splitlines()
    if line <= 0:
        return None

    if line > len(lines):
        return None

    return lines[line - 1]


#error lexico
def t_error(t):
    column = find_column(t.lexer.lexdata, t)
    fragment = get_line_fragment(t.lexer.lexdata, t.lineno)
    error_manager.lexical(f"Caracter no reconocido: '{t.value[0]}'", t.lineno, column, fragment)
    t.lexer.skip(1)

#constructor
lexer = lex.lex()


#Analizador
def tokenize(text):
    error_manager.clear()
    lexer.lineno = 1
    lexer.input(text)
    result = []

    while True:
        token = lexer.token()
        if not token:
            break

        result.append({
            "type": token.type,
            "value": token.value,
            "line": token.lineno,
            "column": find_column(text, token)
        })

    return result


#errores lexicos
def get_lexical_errors():
    return error_manager.to_list()