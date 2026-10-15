# Arquitectura

La aplicación conserva la organización cliente/servidor. `App.tsx` envía el texto por HTTP a Flask. `ExecutionService.execute` elige el compilador o `interpret` según el endpoint. El puerto continúa siendo 2611. No hay servicio externo de compilación.

```mermaid
flowchart LR
    Usuario --> React[Editor React y Vite]
    React -->|JSON source| Flask[Flask 2611]
    Flask --> Service[ExecutionService]
    Service --> Compiler[Compiler]
    Service --> Interpreter[Intérprete P1]
    Compiler --> Runner[QemuRunner]
    Runner --> QEMU[QEMU User]
    QEMU -->|stdout y stderr| Service
    Service --> Reports[HTML y Graphviz]
    Service -->|JSON| React
```

## Flujo de compilación

`Compiler.compile` protege PLY con `analysis_lock`, conserva el AST y copia los errores antes de liberar el bloqueo. `SemanticAnalyzer` registra primero firmas y después recorre todos los cuerpos; admite referencias a funciones posteriores y recursividad. Los mapas de tipos y símbolos se indexan por identidad de nodo y no se agregan al AST, para que los reportes no recorran entornos circulares.

```mermaid
flowchart TD
    Source[Fuente] --> Lexer[Lexer PLY]
    Lexer --> Parser[Parser PLY]
    Parser --> AST[AST compartido]
    AST --> Syntax{Errores de análisis}
    Syntax -->|Sí| Reports[Reportes reales]
    Syntax -->|No| Semantic[SemanticAnalyzer]
    Semantic --> Valid{Tipos y ámbitos válidos}
    Valid -->|No| Reports
    Valid -->|Sí| Visitor[ARM64Visitor]
    Visitor --> Generator[Generator]
    Generator --> Assembly[Ensamblador directo]
```

## Ejecución nativa

```mermaid
flowchart TD
    Assembly[Texto ARM64 mostrado] --> Temp[program.s en TemporaryDirectory]
    Temp --> As[GNU genera program.o]
    Runtime[runtime.c biblioteca fija] --> RuntimeObj[GNU genera runtime.o]
    As --> Link[Enlace estático con libm y libc]
    RuntimeObj --> Link
    Link --> ELF[Verificar cabecera ELF AArch64]
    ELF --> Choice{Ejecutar}
    Choice -->|No| Done[Respuesta sin consola]
    Choice -->|Sí| Limits[prlimit y timeout]
    Limits --> QEMU[QEMU User]
    QEMU --> Files[stdout y stderr acotados]
    Files --> Response[Consola y código de salida]
    Response --> Cleanup[Eliminar directorio temporal]
```

No se genera C a partir del programa ni código de tres direcciones. El C fijo de runtime es biblioteca de funciones nativas que GCC compila para ARM64. Los operadores, saltos, cortocircuito, funciones y frames del programa se emiten desde Python directamente en ensamblador.

## Análisis semántico

```mermaid
flowchart TD
    AST[AST] --> Signatures[Registrar funciones y retornos]
    Signatures --> Main[Comprobar main único]
    Main --> Params[Crear entorno y parámetros]
    Params --> Walk[Recorrer todos los cuerpos y ramas]
    Walk --> Lookup[Resolver símbolos y shadowing]
    Lookup --> Types[Inferir y comprobar tipos y dimensiones]
    Types --> Flow[Validar mutabilidad y transferencias]
    Flow --> Return[Validar retornos por rutas]
    Return --> Errors{Hay errores}
    Errors -->|Sí| Diagnostics[Acumular diagnóstico sin generar binario]
    Errors -->|No| Maps[Entregar tipos, bindings y frames al Visitor]
```

## Concurrencia y reportes

PLY usa variables globales; un bloqueo reentrante evita cruzar fuentes y errores. Cada ejecución de GNU/QEMU tiene archivos propios. El servicio serializa sus solicitudes, y los endpoints de reportes conservan la semántica anterior: muestran la última ejecución global, no un historial por usuario. La respuesta JSON conserva su AST y símbolos independientes.
