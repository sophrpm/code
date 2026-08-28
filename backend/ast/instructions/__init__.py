#todas las intrucciones que agregué acá se van a usar en el parser.py, de esta manera no rompo todo el código si no funciona algo
from .declaration import Declaration
from .assignment import Assignment
from .print_instruction import PrintInstruction
from .if_instruction import IfInstruction
from .while_instruction import WhileInstruction
from .loop_instruction import LoopInstruction
from .match_instruction import MatchInstruction
from .break_instruction import BreakInstruction
from .continue_instruction import ContinueInstruction
from .return_instruction import ReturnInstruction
from .array_declaration import ArrayDeclaration
from .slice_declaration import SliceDeclaration
from .struct_declaration import StructDeclaration
from ..expressions.struct_instance import StructInstance
from .function_declaration import FunctionDeclaration
from .main_function import MainFunction
from .block_instruction import BlockInstruction