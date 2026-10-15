# Auditoría del repositorio y requisitos

Repositorio inspeccionado: `https://github.com/sophrpm/code.git`. El árbol de trabajo estaba limpio. Se leyeron ambos PDF adjuntos y el prompt de trabajo. Los PDF son requisitos del lenguaje y de entrega; sus instrucciones administrativas (colaboradores, nombre de repositorio y commits) no autorizan cambios remotos.

| Archivo | Función actual | Conservar / Modificar / Agregar | Justificación |
|---|---|---|---|
| backend/analyzer/lexer.py | Tokens PLY, comentarios, escapes y posiciones | Conservar | Reconoce los tipos y operadores necesarios |
| backend/analyzer/parser.py | Construye nodos reales; recupera hasta punto y coma | Modificar | Perdía dimensiones de tipos anidados; no admitía literales de arreglos como expresiones |
| backend/ast/ | Nodos con evaluate/execute, validación dinámica | Conservar y agregar ArrayLiteral | El compilador visita sus atributos sin ejecutar estos métodos |
| backend/interpreter/ | Tipos, resultados, scopes con historial, intérprete | Conservar | Referencia y regresión del Proyecto 1 |
| backend/natives/ | Helpers Python de strings, arreglos, abs y sqrt | Conservar | No producen salida del compilador |
| backend/errors/ | ErrorManager y errores con posición/fragmento | Conservar | Reutilizable por semántica estática |
| backend/reports.py | HTML escapado, DOT recursivo y SVG con dot | Modificar | Limitar duración de Graphviz |
| backend/service.py | Parseo, ejecución Python y últimos reportes | Modificar | Añadir flujo compilación y conservar modo intérprete |
| backend/app.py | API Flask, carga .oxs y puerto 2611 | Modificar | Endpoints de compilación y modo anterior; servicio local |
| frontend/frontend/src/App.tsx | Editor, archivos, consola, reportes | Modificar | Mostrar ARM64, tiempos y modo de ejecución |
| frontend/frontend/src/App.css | Tema oscuro y paneles adaptables | Modificar | Panel de ensamblador sin rehacer interfaz |
| frontend/frontend/package.json | React, TS, Vite | Conservar | No hacen falta frameworks adicionales |
| backend/compiler/ | No existía | Agregar | Semántica, Visitor directo y generador ARM64 |
| backend/runner/ | No existía | Agregar | Ensamblado, enlace y QEMU en directorios temporales |
| tests/, docs/, examples/ | Sin batería automatizada | Agregar | Verificación y documentación reproducible |

## Hallazgos reales

Los nodos mezclaban evaluación y validación, por lo que no sirven como fase semántica sin ejecutar el programa. Se crea análisis estático independiente. El parser conservaba únicamente `data_type` para retornos y elementos de arreglos, perdiendo tamaños internos. No existía emisión de ensamblador ni ejecución QEMU. La tabla del intérprete contiene valores de ejecución; la del compilador debe presentar ubicaciones y tipos estáticos, sin inventar valores finales.

## Diferencias y decisiones

Proyecto 1 interpreta el AST; Proyecto 2 exige traducirlo directamente a ARM64, Stack/Heap y ABI AArch64, ensamblar, enlazar y ejecutar QEMU. Conserva la mayoría de la sintaxis, agrega explícitamente arreglos N-dimensionales y requiere visualizar ensamblador. Structs no tienen sección normativa propia en Proyecto 2: se preservan en el intérprete y se diagnostican si se intentan compilar.

Se prioriza la tabla de valores por defecto y ejemplos de §3.2.3: i32=0, f64=0.0, bool=false, String vacío. Char y arreglos necesitan inicializador; `let x;` no permite inferir un tipo. La frase de §3.3.2 sobre variables no inicializadas no invalida los valores por defecto explícitos.

Las tablas aritméticas rigen en compilación: división i32/i32 produce i32, operaciones mixtas promueven a f64 y módulo f64 usa fmod. Las comparaciones admiten bool/bool, String/String e i32/char según §3.3.6. La nota de repetición permite ambas orientaciones String*i32 e i32*String. Un ejemplo modifica una matriz sin `mut`; se exige `mut` por la regla general.

Se acumulan errores estáticos de ramas y funciones, pero no se emite ejecutable con errores. Los ejemplos que imprimen None después de un error corresponden a comportamiento de interpretación incompatible con código estáticamente válido. No se simula su salida. Vec, iteradores y collect del ejemplo de Strings no aparecen en la gramática ni en la tabla de nativas: se utiliza split y arreglos del lenguaje definido.

Se conserva Flask: el documento admite React/etc. en requisitos de calificación y el pedido exige reutilizar Flask/2611. No se migra a Django por una mención aislada. No se crean commits, pushes ni colaboradores.
