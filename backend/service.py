import time
from .compiler import Compiler
from .compiler.compiler import analysis_lock
from .runner import QemuRunner
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
    def interpret(self, source):
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

    def execute(self, source, run=True, mode='native'):
        with analysis_lock:
            if mode == 'interpreter':
                return self.interpret(source)
            start = time.perf_counter()
            compiled = Compiler().compile(source)
            nodes = compiled.pop('nodes')
            dot_source = ast_to_dot(nodes)
            compiled.update(console=[], ast=dot_source, compilation_time=time.perf_counter() - start, execution_time=0.0, build_time=0.0, exit_code=None, stderr='', commands=[])
            if compiled['success']:
                execution = QemuRunner().run(compiled['assembly'], execute=run)
                compiled.update({key: execution[key] for key in ('execution_time', 'build_time', 'exit_code', 'stderr', 'commands')})
                compiled['console'] = execution['stdout'].splitlines()
                if execution['exit_code'] != 0:
                    compiled['success'] = False
                    compiled['errors'].append({'type': 'Ejecución' if execution['stage'] == 'qemu' else 'Compilación', 'description': execution['stderr'] or f'Proceso terminó con código {execution["exit_code"]}', 'line': 0, 'column': 0, 'fragment': ''})
            self.last_dot = dot_source
            self.last_svg = dot_to_svg(dot_source)
            self.last_errors_html = errors_to_html(compiled['errors'])
            self.last_symbols_html = symbols_to_html(compiled['symbols'])
            self.last_result = compiled
            return compiled
