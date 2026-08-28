from .analyzer.parser import get_analysis_errors, has_errors, parse
from .interpreter.interpreter import Interpreter
from .reports import ast_to_dot, dot_to_svg, errors_to_html, symbols_to_html


class ExecutionService:

    def __init__(self):
        self.last_result = self.empty_result()
        self.last_errors_html = errors_to_html([])
        self.last_symbols_html = symbols_to_html([])
        self.last_dot = ast_to_dot([])
        self.last_svg = dot_to_svg(self.last_dot)

    def empty_result(self):
        return {"success": True, "console": [], "errors": [], "symbols": [], "ast": ""}

    #analiza y ejecuta codigo fuente
    def execute(self, source):
        instructions = parse(source)
        analysis_errors = [error.to_dict() for error in get_analysis_errors()]
        interpreter = Interpreter()

        if not has_errors():
            interpreter.execute(instructions)

        errors = analysis_errors + interpreter.get_errors()
        symbols = interpreter.get_all_symbols()
        dot_source = ast_to_dot(instructions)
        self.last_svg = dot_to_svg(dot_source)
        self.last_dot = dot_source
        self.last_errors_html = errors_to_html(errors)
        self.last_symbols_html = symbols_to_html(symbols)
        self.last_result = {
            "success": len(errors) == 0,
            "console": interpreter.get_console(),
            "errors": errors,
            "symbols": symbols,
            "ast": dot_source
        }
        return self.last_result
