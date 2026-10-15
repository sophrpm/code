from dataclasses import asdict
from threading import RLock
from ..analyzer.parser import parse, get_analysis_errors
from .semantic import SemanticAnalyzer
from .visitor import ARM64Visitor
from .types import name

#PLY conserva estado global; protegemos análisis entre solicitudes
analysis_lock = RLock()


class Compiler:
    def compile(self, source):
        with analysis_lock:
            nodes = parse(source)
            errors = [error.to_dict() for error in get_analysis_errors()]
        semantic = SemanticAnalyzer(source)
        if not errors:
            semantic.analyze(nodes)
            errors.extend(semantic.errors.to_list())
        assembly = ARM64Visitor(semantic).generate() if not errors else ''
        symbols = []
        for symbol in semantic.symbols:
            record = asdict(symbol)
            record['data_type'] = name(symbol.data_type)
            record['value'] = '—' if symbol.kind == 'function' else f'Stack [x29 - {symbol.offset}]'
            symbols.append(record)
        return {'success': not errors, 'errors': errors, 'symbols': symbols, 'assembly': assembly, 'nodes': nodes}
