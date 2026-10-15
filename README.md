# OxigenNative · Proyecto 2

Compilador académico de un lenguaje inspirado en Rust. Reutiliza el lexer PLY, el parser, los nodos AST, Flask (puerto **2611**), React/Vite y los reportes de OxigenScript. El intérprete del Proyecto 1 sigue disponible.

El flujo nativo es **fuente → PLY → AST → semántica estática → Visitor ARM64 → GNU assembler → enlace estático → ELF AArch64 → QEMU → consola**. Python no evalúa los programas compilados. La biblioteca `runtime.c` implementa operaciones nativas de Heap, Strings, arreglos e impresión; no recibe código fuente ni AST.

## Instalación en Ubuntu

Requiere Python 3.10+, Node.js 22.12+ y npm. Instale Node con su método habitual si el paquete de Ubuntu es anterior a esa versión.

```bash
sudo apt update
sudo apt install python3-venv graphviz gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu qemu-user libc6-dev-arm64-cross util-linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Compruebe `aarch64-linux-gnu-gcc --version`, `qemu-aarch64 --version` y `dot -V`. Las variables opcionales `OXIGEN_GCC` y `OXIGEN_QEMU` seleccionan ejecutables alternativos. No se requieren servicios remotos para compilar.

## Iniciar la aplicación

Desde la raíz:

```bash
source .venv/bin/activate
python -m backend.app
```

En otra terminal:

```bash
cd frontend/frontend
npm ci
npm run dev
```

Abra la dirección indicada por Vite. El backend escucha en `127.0.0.1:2611`. Para cambiar su URL cree `frontend/frontend/.env` con `VITE_API_URL=http://localhost:2611`.

Seleccione **ARM64 / QEMU**, abra `examples/demo.oxs` y pulse **Compilar** (ensambla y enlaza) o **Ejecutar** (además ejecuta QEMU). El panel muestra exactamente el ensamblador entregado al runner y separa los tiempos de análisis/generación, construcción del binario y ejecución. Seleccione **Intérprete P1** para ejecutar el flujo anterior.

## Ejemplo y ejecución sin interfaz

```rust
fn sumar(a: i32, b: i32) -> i32 { return a + b; }
fn main() { println!("Resultado: {}", sumar(10, 20)); }
```

Salida real esperada: `Resultado: 30`.

```bash
python - <<'PY'
from pathlib import Path
from backend.service import ExecutionService
result = ExecutionService().execute(Path('examples/demo.oxs').read_text())
Path('/tmp/program.s').write_text(result['assembly'])
print('\n'.join(result['console']))
print(result['errors'])
PY
```

Para ensamblar manualmente ese archivo generado:

```bash
aarch64-linux-gnu-gcc -c /tmp/program.s -o /tmp/program.o
aarch64-linux-gnu-gcc -O2 -c backend/compiler/runtime.c -o /tmp/runtime.o
aarch64-linux-gnu-gcc -static /tmp/program.o /tmp/runtime.o -lm -o /tmp/program
qemu-aarch64 /tmp/program
```

La API utiliza directorios temporales separados y límites de tiempo, CPU, Heap, Stack, espacio virtual y salida. Estos límites son para uso académico local; QEMU User y `prlimit` no constituyen aislamiento de un servidor público multiusuario.

## API

| Método | Ruta | Comportamiento |
|---|---|---|
| GET | `/api/health` | Estado HTTP |
| POST | `/api/compile` | Analizar, generar, ensamblar y enlazar sin ejecutar |
| POST | `/api/execute` | Compilar y ejecutar QEMU |
| POST | `/api/interpret` | Intérprete original |
| POST | `/api/files` | Cargar archivo UTF-8 `.oxs` |
| GET | `/api/reports/errors` | HTML de errores |
| GET | `/api/reports/symbols` | HTML de símbolos |
| GET | `/api/reports/ast.dot` | AST real en DOT |
| GET | `/api/reports/ast.svg` | AST real en SVG |

Los tres endpoints de procesamiento reciben `{"source":"fn main(){...}"}`. La respuesta incluye `success`, `console`, `errors`, `symbols`, `ast`, `assembly`, `compilation_time`, `build_time`, `execution_time`, `exit_code`, `stderr` y `commands`. La lista `commands` permite revisar ensamblado, enlace y ejecución; las rutas temporales expiran al terminar. Los reportes HTTP corresponden a la última solicitud atendida.

## Estructura

```text
backend/analyzer/       Lexer y parser PLY compartidos
backend/ast/            AST compartido; intérprete preservado
backend/interpreter/    Ejecución original
backend/compiler/       Tipos, entornos, semántica, Visitor, generador y runtime
backend/runner/         GNU y QEMU
backend/service.py      Coordina ambos modos y reportes
frontend/frontend/      Editor React/Vite existente
examples/               Programa y ensamblador reproducible
tests/                  Casos estáticos, nativos, regresión y API
docs/                   Auditoría, diseño, manuales y evidencias
```

## Verificación

```bash
python -m unittest discover -s tests -v
cd frontend/frontend
npm run build
npm run lint
```

Las pruebas nativas se omiten explícitamente si faltan herramientas; esa omisión no equivale a aprobación. Consulte [resultados](docs/PRUEBAS.md).

## Documentación y alcance

- [Auditoría y diferencias entre proyectos](docs/AUDITORIA_PROYECTO1_PROYECTO2.md)
- [Cambios y correcciones](docs/CAMBIOS_PROYECTO2.md)
- [Arquitectura y flujos](docs/ARQUITECTURA.md)
- [Clases y métodos](docs/CLASES_Y_METODOS.md)
- [Generación ARM64 y memoria](docs/GENERACION_ARM64.md)
- [Gramática real](docs/GRAMATICA.md)
- [Manual técnico](docs/MANUAL_TECNICO.md)
- [Manual de usuario](docs/MANUAL_USUARIO.md)

Se implementan los tipos primitivos, arreglos N-dimensionales contiguos, slices por referencia, funciones recursivas y la tabla de nativas del Proyecto 2. Structs y las extensiones `push/remove` permanecen en el intérprete; el compilador las rechaza expresamente. Vec, iteradores y collect no forman parte de la gramática. Los límites y decisiones adicionales están detallados en el manual técnico. No se afirma equivalencia total con Rust.
