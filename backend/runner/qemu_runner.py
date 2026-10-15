import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


class QemuRunner:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.gcc = os.environ.get('OXIGEN_GCC', 'aarch64-linux-gnu-gcc')
        self.qemu = os.environ.get('OXIGEN_QEMU', 'qemu-aarch64')
        self.runtime = Path(__file__).resolve().parents[1] / 'compiler' / 'runtime.c'

    def available(self):
        return bool(shutil.which(self.gcc) and shutil.which(self.qemu) and shutil.which('prlimit'))

    def run(self, assembly, execute=True):
        start = time.perf_counter()
        result = {'stdout': '', 'stderr': '', 'exit_code': None, 'execution_time': 0.0, 'build_time': 0.0, 'commands': [], 'stage': 'herramientas'}
        if not self.available():
            result['stderr'] = 'Faltan aarch64-linux-gnu-gcc, qemu-aarch64 o prlimit. Consulte README.md.'
            return result
        try:
            with tempfile.TemporaryDirectory(prefix='oxigennative-') as directory:
                root = Path(directory)
                source, obj, runtime_obj, binary = [root / name for name in ('program.s', 'program.o', 'runtime.o', 'program')]
                source.write_text(assembly, encoding='utf-8')
                commands = [('ensamblaje', [self.gcc, '-c', str(source), '-o', str(obj)]), ('biblioteca', [self.gcc, '-std=c11', '-O2', '-c', str(self.runtime), '-o', str(runtime_obj)]), ('enlace', [self.gcc, '-static', str(obj), str(runtime_obj), '-lm', '-o', str(binary)])]
                for stage, command in commands:
                    result['stage'] = stage
                    result['commands'].append(command)
                    process = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
                    if process.returncode:
                        result.update(stderr=process.stderr, exit_code=process.returncode)
                        return result
                header = binary.read_bytes()[:20]
                if header[:4] != b'\x7fELF' or int.from_bytes(header[18:20], 'little') != 183:
                    result.update(stage='enlace', stderr='El ejecutable no es ELF AArch64')
                    return result
                result['architecture'] = 'AArch64'
                result['build_time'] = time.perf_counter() - start
                if not execute:
                    result.update(stage='compilado', exit_code=0)
                    return result
                result['stage'] = 'qemu'
                command = ['prlimit', '--cpu=3', '--as=1073741824', '--stack=8388608', '--fsize=1048576', '--core=0', '--', self.qemu, '-R', '268435456', str(binary)]
                result['commands'].append(command)
                run_start = time.perf_counter()
                #archivos acotados por RLIMIT_FSIZE, sin pipes de salida ilimitados
                with (root / 'stdout').open('w+b') as output, (root / 'stderr').open('w+b') as errors:
                    process = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors, timeout=self.timeout, check=False, cwd=root)
                    output.seek(0)
                    errors.seek(0)
                    result.update(stdout=output.read(1048576).decode('utf-8', errors='replace'), stderr=errors.read(1048576).decode('utf-8', errors='replace'), exit_code=process.returncode)
                result['execution_time'] = time.perf_counter() - run_start
        except subprocess.TimeoutExpired:
            result['stderr'] = f'Tiempo límite excedido durante {result["stage"]}'
        except OSError as error:
            result['stderr'] = f'No se pudo ejecutar la herramienta: {error}'
        return result
