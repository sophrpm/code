from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import random
import json
import unittest
from unittest.mock import patch
from backend.app import app
from backend.compiler import Compiler
from backend.runner import QemuRunner
from backend.service import ExecutionService


class IntegrationTests(unittest.TestCase):
    def test_interpreter_integral(self):
        random.seed(2611)
        result = ExecutionService().execute(Path('test_oxigenscript.oxs.txt').read_text(), mode='interpreter')
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['console']), 108)
        self.assertEqual(result['console'], json.loads(Path('tests/fixtures/project1_console.json').read_text()))
        self.assertIn('Hola Mundo', result['console'])

    def test_reports(self):
        service = ExecutionService()
        result = service.execute('fn main(){let x=3;println!(x);}', mode='interpreter')
        self.assertTrue(result['success'])
        self.assertIn('Declaration', result['ast'])
        self.assertIn('x', service.last_symbols_html)
        self.assertIn('<svg', service.last_svg)

    def test_api_validation(self):
        client = app.test_client()
        self.assertEqual(client.post('/api/execute', json={}).status_code, 400)
        self.assertEqual(client.post('/api/execute', json={'source': 1}).status_code, 400)
        self.assertEqual(client.get('/api/health').status_code, 200)

    @unittest.skipUnless(QemuRunner().available(), 'Requiere GNU y QEMU')
    def test_api_native(self):
        client = app.test_client()
        source = 'fn main(){println!(42);}'
        compile_result = client.post('/api/compile', json={'source': source}).get_json()
        self.assertTrue(compile_result['success'], compile_result['errors'])
        self.assertEqual(compile_result['console'], [])
        result = client.post('/api/execute', json={'source': source}).get_json()
        self.assertTrue(result['success'], result['errors'])
        self.assertEqual(result['console'], ['42'])
        self.assertEqual(result['assembly'], compile_result['assembly'])
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(client.get('/api/reports/ast.svg').status_code, 200)
        self.assertEqual(client.get('/api/reports/symbols').status_code, 200)
        self.assertEqual(client.post('/api/interpret', json={'source': source}).get_json()['console'], ['42'])

    def test_missing_tools(self):
        with patch.dict('os.environ', {'OXIGEN_GCC': '/missing/compiler'}):
            result = QemuRunner().run('')
        self.assertIsNone(result['exit_code'])
        self.assertIn('Faltan', result['stderr'])

    def test_concurrent_analysis(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda i: Compiler().compile(f'fn main(){{let x={i};println!(x);}}'), range(12)))
        self.assertTrue(all(result['success'] for result in results))

    def test_native_never_calls_interpreter(self):
        with patch('backend.service.Interpreter', side_effect=AssertionError('No interpretar')):
            self.assertTrue(Compiler().compile('fn main(){println!(1);}')['success'])


if __name__ == '__main__':
    unittest.main()
