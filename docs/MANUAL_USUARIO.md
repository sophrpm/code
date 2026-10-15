# Manual de usuario

## Instalación e inicio

1. Instale los paquetes Ubuntu y cree el entorno virtual siguiendo [README](../README.md#instalación-en-ubuntu).
2. Desde la raíz, active `.venv` y ejecute `python -m backend.app`.
3. En otra terminal entre a `frontend/frontend`, ejecute `npm ci` y `npm run dev`.
4. Abra la dirección que muestra Vite. La barra debe indicar Backend conectado.

## Archivos y editor

Pulse **Nuevo** para vaciar el editor. **Abrir .oxs** lee un archivo UTF-8 local y conserva su nombre; **Guardar** descarga el contenido actual con extensión `.oxs`. La columna izquierda indica números de línea y acompaña el desplazamiento vertical del editor. El archivo de ejemplo está en `examples/demo.oxs`.

Escriba un programa con una única función main:

```rust
fn main() {
    let mut contador: i32 = 0;
    while contador < 3 {
        println!("Contador: {}", contador);
        contador += 1;
    }
}
```

## Compilar y ejecutar

Seleccione **ARM64 / QEMU**. **Compilar** realiza análisis, generación, ensamblaje y enlace sin ejecutar. **Ejecutar** repite la compilación del texto actual y lanza el ejecutable con QEMU. El código que se ve a la derecha coincide con el `.s` utilizado para construir el binario.

La consola muestra las líneas producidas por println!. El ejemplo anterior imprime Contador: 0, Contador: 1 y Contador: 2. Bajo el editor aparecen los tiempos y el código de salida; 0 indica que el proceso terminó correctamente. La salida se muestra cuando la solicitud termina, no como streaming.

Seleccione **Intérprete P1** para usar el proyecto anterior, incluidos structs y extensiones de arreglos. Ese modo no genera ARM64. Cada ejecución reemplaza los resultados previos de la interfaz.

## Reportes

- **Errores**: tipo, descripción y posición. Los reportes HTML incluyen además el fragmento de fuente.
- **Símbolos**: funciones, parámetros y variables reales del análisis, con tipo y ámbito. En modo nativo el HTML muestra la ubicación de Stack y no un valor final de ejecución.
- **AST**: fuente DOT real y enlaces para abrir SVG o descargar DOT. Si falta Graphviz, DOT permanece disponible y el SVG informa que no se pudo generar.

Los enlaces de reportes corresponden al último programa procesado por el backend. Si otra ventana ejecuta un programa, reemplaza esos reportes.

## Interpretar problemas

Un error léxico suele indicar un carácter no válido o comentario sin cerrar. Un error sintáctico requiere revisar puntuación y delimitadores. Un error semántico puede indicar nombre no declarado, tipo incompatible, mutabilidad o dimensiones incorrectas. Corrija todos los errores estáticos antes de ejecutar.

Un diagnóstico de compilación que menciona herramientas faltantes se resuelve instalando GNU AArch64, QEMU y util-linux. Un error de enlace requiere revisar la instalación de libc ARM64. Un error de ejecución con índice o división indica una condición detectada por el binario. Un tiempo límite puede indicar un bucle infinito o un programa demasiado costoso para los límites configurados.

## Sesión reproducible

Abra `examples/demo.oxs` y ejecute. Su consola debe contener:

```text
OxigenNative en ARM64
Fibonacci(10): 55
Matriz: [[1, 2, 3], [4, 5, 7]]
Slice: [4, 5]
Hola ARM64
Palabras: ["Hola", "Mundo"]
División: 3.5
```

Captura real de Chromium después de compilar y ejecutar el ejemplo mediante la interfaz:

![OxigenNative ejecutando ARM64 con QEMU](capturas/oxigennative-qemu.png)

Las evidencias automatizadas están en [PRUEBAS](PRUEBAS.md).
