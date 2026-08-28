# OxigenScript

Intérprete académico de un lenguaje inspirado en Rust. El backend usa Python, PLY y Flask; la interfaz usa React con Vite. El flujo de ejecución es: código `.oxs` → lexer PLY → parser PLY → AST → intérprete → consola y reportes.

## Requisitos en Ubuntu

- Python 3.10 o posterior
- Node.js 20 o posterior y npm
- Graphviz (ejecutable `dot`)

```bash
sudo apt update
sudo apt install python3-venv graphviz nodejs npm
```

## Backend

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m backend.app
```

La API queda disponible en `http://localhost:2611`. Endpoints principales:

| Método | Ruta | Uso |
| --- | --- | --- |
| GET | `/api/health` | Estado del servidor |
| POST | `/api/execute` | Analiza y ejecuta JSON con `{ "source": "..." }` |
| POST | `/api/files` | Carga multipart de un archivo `.oxs` UTF-8 |
| GET | `/api/reports/errors` | Reporte HTML de la última ejecución |
| GET | `/api/reports/symbols` | Tabla de símbolos HTML |
| GET | `/api/reports/ast.dot` | Fuente Graphviz del AST real |
| GET | `/api/reports/ast.svg` | Representación SVG generada por Graphviz |

## Frontend

En otra terminal:

```bash
cd frontend/frontend
npm install
npm run dev
```

Abra la dirección indicada por Vite. La URL del backend se puede cambiar creando `frontend/frontend/.env`:

```text
VITE_API_URL=http://localhost:2611
```

La barra superior permite crear, abrir y guardar archivos `.oxs`, además de analizar/ejecutar el editor. La parte inferior muestra la consola y las pestañas de errores, símbolos y AST. Los enlaces de reportes abren los HTML y el gráfico correspondientes a la ejecución más reciente.

## Gramática y comportamiento

La gramática PLY está en `backend/analyzer/parser.py` y el lexer en `backend/analyzer/lexer.py`. Se soportan declaraciones estáticas e inferidas, shadowing, mutabilidad, operadores, bloques, `if`, `while`, `loop`, etiquetas, `match`, transferencias, arreglos, slices por referencia, strings, structs anidados, funciones y nativas. Las funciones y structs se registran antes de ejecutar `main`, por lo que una función puede invocarse antes de aparecer en el archivo.

El manejo compartido registra errores léxicos, sintácticos y semánticos con tipo, descripción, línea, columna y fragmento cuando está disponible. La tabla de símbolos se obtiene del historial real de scopes, no de un recorrido simulado del AST.

## Archivo integral

El archivo incluido se llama `test_oxigenscript.oxs.txt` porque conserva el sufijo recibido en el material. Para cargarlo desde la interfaz, guarde una copia con extensión `.oxs`; el contenido original no necesita modificarse. Para probarlo directamente desde Python:

```bash
python - <<'PY'
from backend.service import ExecutionService
source = open("test_oxigenscript.oxs.txt", encoding="utf-8").read()
result = ExecutionService().execute(source)
print("\n".join(result["console"]))
print(result["errors"])
PY
```

## Decisiones y observación del material

- Los slices conservan una referencia al arreglo original mediante `array`, `start` y `end`.
- El archivo DOT siempre está disponible. El SVG requiere además el paquete del sistema `graphviz`.
- El PDF enumera Django en la sección de herramientas, pero describe una API REST y el repositorio ya estaba iniciado con Flask. Se conservó Flask, según la arquitectura existente y los requisitos de continuación del proyecto.
- La sección `RESULTADO ESPERADO` del archivo integral omite algunas salidas que sí aparecen en sus propios casos (por ejemplo varios métodos de String) y muestra `""` para imprimir el String vacío. El intérprete sigue la semántica del PDF: `println!` imprime el contenido del String, por lo que un String vacío produce una línea vacía, y ejecuta todas las llamadas presentes en el código.
