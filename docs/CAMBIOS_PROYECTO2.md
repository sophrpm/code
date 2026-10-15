# Cambios del Proyecto 2

Base inspeccionada: commit `904cfa22afe8e1f1e747e9ed3544590a94356dc0` de sophrpm/code. No se crearon commits ni pushes.

## Archivos conservados

Se mantienen el lexer, ErrorManager, tipos y entornos del intérprete, las expresiones e instrucciones previas salvo Declaration, todas las nativas Python y su comportamiento de referencia, el flujo React/Vite y los reportes HTML/DOT/SVG. No se eliminó ningún archivo original. El intérprete es accesible en `/api/interpret` y en la selección de modo de React.

## Tabla de cambios

| Módulo / archivo | Cambio | Motivo y dependencias | Pruebas realizadas |
|---|---|---|---|
| analyzer/parser.py | Literales de arreglos como primarios; tipos recursivos y retornos completos | Reutiliza AST; evita perder dimensiones | Parser, matrices 2D/3D, retornos y parámetros |
| ast/expressions/array_literal.py, nuevo | Nodo de literal/repetición | Permite anidamiento sin parser duplicado | Literales, repetición evaluada una sola vez |
| ast/instructions/declaration.py | Delega literales al ArrayDeclaration original y conserva metadatos de arreglos | Mantiene validación dinámica del intérprete | Regresión integral de 108 líneas |
| compiler/types.py, nuevo | Tipos recursivos, nombres, anchuras y compatibilidad | Uso común entre semántica y generación | Tipos, dimensiones y promociones |
| compiler/environment.py, nuevo | Entorno y Symbol con offsets | Ámbitos estáticos, shadowing y reportes | Scopes, mutabilidad y símbolos |
| compiler/semantic.py, nuevo | Análisis completo sin ejecución Python | ErrorManager; mapas por identidad de nodo | Casos negativos, ramas no tomadas, funciones no invocadas |
| compiler/generator.py, nuevo | Emisión de secciones, instrucciones, constantes y descriptores | Produce texto GNU AArch64 | Ensamblado real de todos los casos válidos |
| compiler/visitor.py, nuevo | Traducción directa del AST | Usa mapas semánticos y runtime | Control, llamadas, ABI, recursión, arreglos y nativas |
| compiler/runtime.c, nuevo | Biblioteca fija AArch64 de memoria, Strings, arreglos e impresión | libc/libm; no recibe AST ni fuente | QEMU, límites y Unicode básico |
| compiler/compiler.py, nuevo | Orquesta PLY, semántica y Visitor | Bloqueo reentrante de PLY | Concurrencia, errores, ausencia de interpretación |
| runner/qemu_runner.py, nuevo | GNU, enlace, ELF, QEMU y límites | subprocess sin shell y TemporaryDirectory | Ejecución, timeout, salida acotada, herramientas faltantes |
| service.py | Modo nativo por defecto, `interpret` preservado | Compiler, QemuRunner y reportes | API y regresión |
| app.py | Endpoints compile/interpret, límite de fuente, inicio local sin debug | Flask y servicio existente; puerto 2611 | Test client y navegador real |
| reports.py | Timeout de Graphviz | Misma generación HTML/DOT/SVG | AST real y HTML |
| App.tsx, App.css | Selector de modo, ARM64, compilar, tiempos y numeración sincronizada | React original, sin dependencias nuevas | Build, lint y Chromium con captura |
| tests/, examples/, docs/, README.md, .gitignore | Casos reproducibles, ejemplo real y documentación | unittest y herramientas del sistema | Ver PRUEBAS.md |

Los `__init__.py` nuevos exportan las clases Compiler y QemuRunner; no contienen implementaciones ficticias.

## Problemas encontrados y corregidos

1. El parser descartaba el tipo interno de arreglos anidados y el tipo completo de retorno. Ahora conserva `nested_type`, `type_info` y `return_info`.
2. Las listas solo aparecían en declaraciones. Ahora son expresiones primarias y se pueden anidar/pasar/retornar.
3. La evaluación del AST estaba unida a la validación. Se añadió una fase estática separada que detecta errores incluso en ramas no ejecutadas.
4. La consola solo podía venir de Python. El flujo nativo captura stdout de un ELF AArch64 verificado y ejecutado por QEMU.
5. La primera versión del prólogo podía pisar x0 antes de guardar parámetros. Se corrigió para direccionar slots con x9/x10 sin tocar argumentos pendientes; se probaron diez argumentos y mezcla de bancos.
6. Una promoción de arreglos no puede reinterpretar bits i32 como f64. Se convierten los elementos de literales en generación y se rechazan conversiones implícitas entre variables con bloques incompatibles.
7. Se añadieron límites de Heap, índices, tamaños y salida, así como timeout de procesos y Graphviz. La lectura de salida truncada reemplaza secuencias UTF-8 incompletas en lugar de fallar el servicio.
8. Este entorno no permitía instalación de sistema y no tenía GNU/QEMU. Se descargaron paquetes Debian y extrajeron en `/workspace/toolchain`; un wrapper selecciona sysroot y bibliotecas sin modificar el sistema. La instalación Ubuntu estándar está en README.
9. En la preparación local hubo errores reales de bibliotecas compartidas, rutas absolutas de libm y compatibilidad de punteros del runtime. Se corrigieron antes de registrar pruebas aprobadas.

## Alcance pendiente

El [manual técnico](MANUAL_TECNICO.md#límites-conocidos-y-pendientes) registra las limitaciones. No se compilan structs ni push/remove del intérprete; no se incluyen Vec/iteradores ni ownership de Rust. Las expansiones Unicode de varios caracteres y la lectura de valores finales de símbolos no están implementadas. No se desplegó un servicio público ni se realizaron operaciones administrativas en GitHub.
