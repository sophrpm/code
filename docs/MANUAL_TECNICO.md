# Manual técnico

## Objetivo y decisiones

OxigenNative amplía OxigenScript sin eliminar el intérprete. El lenguaje de implementación del compilador es Python con PLY. El programa de entrada se convierte directamente de AST a GNU AArch64; no se transpila a C y no utiliza representación intermedia de tres direcciones. Las rutinas fijas de biblioteca se escriben en C para usar memoria, Unicode, libc y libm con la ABI nativa. GCC compila esa biblioteca, ensambla el `.s` del programa y enlaza un ELF estático. Toda salida de consola nativa procede de QEMU.

La arquitectura y los seis diagramas requeridos están en [ARQUITECTURA](ARQUITECTURA.md), [CLASES_Y_METODOS](CLASES_Y_METODOS.md) y [GENERACION_ARM64](GENERACION_ARM64.md). Los diagramas describen las clases reales y el flujo implementado. La gramática completa extraída de PLY se incluye en [GRAMATICA](GRAMATICA.md).

## Semántica estática

La primera pasada recoge funciones y retornos; la segunda visita todos los cuerpos aunque una función nunca se llame o una rama sea inalcanzable. Se comprueban identificadores, ámbitos, shadowing, mutabilidad, firmas, retornos, condiciones bool y transferencias. No se llama al intérprete para descubrir tipos. Las funciones pueden usar otras declaradas después y llamarse recursivamente.

Los tipos escalares son strings; los tipos de arreglos son tuplas `(array, elemento, longitud)`. El elemento puede ser otra tupla. Los slices son `(slice, elemento, None)` y se comprueban en ejecución. Los literales de arreglo se pueden promover de enteros a f64 cuando hay un tipo esperado, incluidas dimensiones anidadas. Una variable de arreglo no se convierte implícitamente a un bloque de diferente tipo de elemento.

Los retornos se verifican de forma conservadora: return directo, bloque que retorna, if con ambas ramas o match con todos los brazos que retornan. Un bucle infinito o un bucle con retorno no se considera prueba suficiente de retorno; se puede escribir un return final explícito. No se implementa un análisis general de terminación.

La [auditoría](AUDITORIA_PROYECTO1_PROYECTO2.md) documenta las inconsistencias de los PDF y las reglas seleccionadas. Un programa con errores estáticos se reporta, pero no produce binario. Los errores dinámicos de límites, división y rango terminan el ejecutable con estado distinto de cero.

## Memoria, registros y biblioteca

Consulte [GENERACION_ARM64](GENERACION_ARM64.md) para layouts, fórmulas Row-Major, prólogo/epílogo, argumentos de Stack y bancos de punto flotante. Los slots uniformes de 8 bytes simplifican el cálculo de offsets. No se utilizan registros preservados sin guardarlos.

La representación de arreglos es consistente entre literales, funciones, submatrices, slices y nativas. `ox_index` verifica cada acceso, `ox_subarray` construye una vista de la dimensión siguiente y `ox_slice` referencia datos sin copiar. `ox_print` recibe un valor y su descriptor, no texto de un AST. Esto permite imprimir arreglos anidados dentro del binario.

## Servicios y errores

`ExecutionService` conserva reportes de la última solicitud y serializa la ejecución. Compiler usa además un bloqueo propio para PLY. Cada llamada a GNU/QEMU recibe listas de argumentos y rutas propias; nunca concatena el código del editor en un shell. QemuRunner configura 5 segundos de timeout, 3 segundos de CPU, 1 GiB de espacio virtual, reserva virtual QEMU de 256 MiB, Stack de 8 MiB y máximo de 1 MiB por archivo de salida. El Heap de la biblioteca tiene límite acumulado de 64 MiB. Los procesos de construcción tienen timeout de 20 segundos por etapa. Graphviz tiene timeout de 10 segundos.

QEMU User no es una frontera de aislamiento. El backend se inicia solo en loopback y sin debug. Un despliegue público necesitaría un contenedor o sandbox adicional, cuotas por usuario y autenticación. No se publica el servicio.

Los errores léxicos y sintácticos provienen de PLY; los semánticos reutilizan ErrorManager con línea, columna y fragmento. Los errores de GNU y QEMU se registran con fase y stderr; al provenir de procesos externos, sus posiciones del lenguaje son 0. Los reportes HTML escapan contenido del usuario.

## Límites conocidos y pendientes

- Structs y las extensiones mutables de tamaño `push/remove` del Proyecto 1 se conservan en el intérprete y no se compilan; no pertenecen a la tabla normativa de nativas del Proyecto 2.
- Vec, referencias tipadas como `&str`, iteradores, `collect`, `split_whitespace`, closures y ownership de Rust no forman parte de la gramática implementada.
- El parser compartido no admite etiquetas en while ni rangos abiertos; las etiquetas se admiten en loop como la gramática del documento.
- No se infiere un tipo a partir de una asignación posterior a `let x;`. Char y arreglos sin valor se rechazan; los demás tipos usan los valores por defecto documentados.
- Los símbolos del compilador muestran tipos/ámbitos/ubicación de Stack; no se leen valores finales del proceso QEMU. El campo Valor del reporte identifica una ubicación estática.
- Las asignaciones entre variables de arreglo comparten descriptor; `clone` copia el bloque. No se simula el movimiento y los préstamos exclusivos de Rust.
- El Heap se recupera al terminar el proceso, sin liberación individual; repetir muchas operaciones de Strings o vistas puede alcanzar el límite aunque algunos resultados ya no sean accesibles.
- Strings utilizan NUL como terminador y no admiten NUL incrustado en su contenido. La conversión de mayúsculas/minúsculas no hace expansiones Unicode de múltiples puntos de código.
- La impresión f64 usa 15 dígitos significativos. No pretende coincidir en todos los detalles con el formateador de Rust.
- El análisis de retornos y de índices constantes es conservador; no se propagan constantes por variables ni se prueban invariantes de bucles.
- Los enlaces de reportes muestran la última ejecución global; no son sesiones multiusuario.
- La prueba de navegador cubre compilación, QEMU, consola, tiempos, símbolos, AST y ancho móvil. Abrir/guardar archivos mediante los diálogos del sistema queda como comprobación manual adicional.

## Mantenimiento y defensa

Para agregar una instrucción, primero añada/ajuste su producción PLY y el nodo AST; después implemente validación en SemanticAnalyzer y generación en ARM64Visitor. Si necesita una operación del runtime, defina una función nativa con parámetros ABI claros y documente su layout. Añada una prueba que recorra todo el flujo y compruebe stdout/código de salida; los errores estáticos deben comprobar que assembly queda vacío.

Una defensa puede seguir `examples/demo.oxs`: observar el AST real, ubicar el tipo y offset de cada símbolo, identificar las etiquetas de Fibonacci y su frame, explicar las dos llamadas recursivas y cómo sus temporales sobreviven en Stack, y finalmente mostrar el acceso Row-Major de la matriz y la vista del slice.
