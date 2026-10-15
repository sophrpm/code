#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <locale.h>
#include <wchar.h>
#include <wctype.h>
#include <time.h>
#include <unistd.h>

//las rutinas son biblioteca nativa; no reciben AST ni código fuente
//tipo: categoría, bytes por valor, tipo hijo y longitud estática
 typedef struct Type { int64_t kind, size; struct Type *child; int64_t length; } Type;
 typedef struct Array { int64_t length; unsigned char *data; Type *element; } Array;
static Type char_type = {4, 8, NULL, 0};
static Type string_type = {5, 8, NULL, 0};
static size_t allocated = 0;

static void fail(const char *message) {
    fprintf(stderr, "[Ejecución] %s\n", message);
    exit(1);
}
void ox_zero(void) { fail("División o módulo entre cero"); }
void ox_negative(void) { fail("sqrt no acepta valores negativos"); }
void ox_init(void) { setlocale(LC_ALL, "C.UTF-8"); srand((unsigned)time(NULL) ^ (unsigned)getpid()); }
static void *allocate(size_t count) {
    if (count > 64 * 1024 * 1024 || allocated + count > 64 * 1024 * 1024) fail("Límite del Heap excedido");
    void *result = calloc(count ? count : 1, 1);
    if (!result) fail("Memoria insuficiente");
    allocated += count;
    return result;
}
char *ox_string_copy(const char *text) {
    size_t size = strlen(text) + 1;
    char *result = allocate(size);
    memcpy(result, text, size);
    return result;
}
static int64_t utf8_next(const unsigned char **text) {
    const unsigned char *s = *text;
    int64_t value = *s++;
    int count = 0;
    if (value >= 240) { value &= 7; count = 3; }
    else if (value >= 224) { value &= 15; count = 2; }
    else if (value >= 192) { value &= 31; count = 1; }
    while (count-- && *s) value = (value << 6) | (*s++ & 63);
    *text = s;
    return value;
}
static int utf8_write(char *out, int64_t c) {
    if (c < 128) { out[0] = c; return 1; }
    if (c < 2048) { out[0] = 192 | (c >> 6); out[1] = 128 | (c & 63); return 2; }
    if (c < 65536) { out[0] = 224 | (c >> 12); out[1] = 128 | ((c >> 6) & 63); out[2] = 128 | (c & 63); return 3; }
    out[0] = 240 | (c >> 18); out[1] = 128 | ((c >> 12) & 63); out[2] = 128 | ((c >> 6) & 63); out[3] = 128 | (c & 63); return 4;
}
char *ox_char_string(int64_t value) {
    char *result = allocate(5);
    utf8_write(result, value);
    return result;
}
int64_t ox_strlen(const char *text) {
    int64_t count = 0;
    const unsigned char *s = (const unsigned char *)text;
    while (*s) { utf8_next(&s); count++; }
    return count;
}
char *ox_concat(const char *a, const char *b) {
    size_t first = strlen(a), second = strlen(b);
    char *result = allocate(first + second + 1);
    memcpy(result, a, first); memcpy(result + first, b, second + 1);
    return result;
}
char *ox_repeat(const char *text, int64_t count) {
    if (count < 0) fail("No se puede repetir un String una cantidad negativa");
    size_t size = strlen(text);
    if (count > 64 * 1024 * 1024 || size && (uint64_t)count > (64 * 1024 * 1024) / size) fail("Repetición demasiado grande");
    char *result = allocate(size * count + 1);
    for (int64_t i = 0; i < count; i++) memcpy(result + i * size, text, size);
    return result;
}
int64_t ox_contains(const char *text, const char *part) { return strstr(text, part) != NULL; }
char *ox_replace(const char *text, const char *from, const char *to) {
    size_t source = strlen(from), dest = strlen(to), size = strlen(text), count = 0;
    if (!source) {
        int64_t chars = ox_strlen(text);
        char *result = allocate(size + (chars + 1) * dest + 1), *out = result;
        const unsigned char *cursor = (const unsigned char *)text;
        memcpy(out, to, dest); out += dest;
        while (*cursor) {
            const unsigned char *start = cursor;
            utf8_next(&cursor);
            size_t bytes = cursor - start;
            memcpy(out, start, bytes); out += bytes;
            memcpy(out, to, dest); out += dest;
        }
        return result;
    }
    const char *cursor = text, *found;
    while ((found = strstr(cursor, from))) { count++; cursor = found + source; }
    size_t total = size - count * source + count * dest;
    char *result = allocate(total + 1), *out = result;
    cursor = text;
    while ((found = strstr(cursor, from))) {
        size_t prefix = found - cursor;
        memcpy(out, cursor, prefix); out += prefix;
        memcpy(out, to, dest); out += dest;
        cursor = found + source;
    }
    strcpy(out, cursor);
    return result;
}
static char *change_case(const char *text, int upper) {
    char *result = allocate(strlen(text) * 4 + 1), *out = result;
    const unsigned char *cursor = (const unsigned char *)text;
    while (*cursor) {
        int64_t c = utf8_next(&cursor);
        out += utf8_write(out, upper ? towupper(c) : towlower(c));
    }
    return result;
}
char *ox_upper(const char *text) { return change_case(text, 1); }
char *ox_lower(const char *text) { return change_case(text, 0); }
Array *ox_array_new(int64_t length, Type *element) {
    if (length < 0 || length > 8388608 || element->size < 0 || (uint64_t)element->size > 64 * 1024 * 1024 || length && (uint64_t)element->size > (64 * 1024 * 1024) / length) fail("Tamaño de arreglo inválido");
    Array *array = allocate(sizeof(Array));
    array->length = length; array->element = element;
    array->data = allocate(length * element->size);
    return array;
}
void *ox_index(Array *array, int64_t index) {
    if (index < 0 || index >= array->length) fail("Índice fuera de los límites del arreglo");
    return array->data + index * array->element->size;
}
Array *ox_subarray(Array *array, int64_t index) {
    Type *type = array->element;
    Array *result = allocate(sizeof(Array));
    result->data = ox_index(array, index); result->length = type->length; result->element = type->child;
    return result;
}
Array *ox_slice(Array *array, int64_t start, int64_t end) {
    if (start < 0 || end < start || end > array->length) fail("Rango de slice fuera de los límites");
    Array *result = allocate(sizeof(Array));
    result->length = end - start; result->data = array->data + start * array->element->size; result->element = array->element;
    return result;
}
void ox_array_set(Array *array, int64_t index, uint64_t value) {
    void *dest = ox_index(array, index);
    if (array->element->kind == 6) {
        Array *source = (Array *)value;
        memcpy(dest, source->data, array->element->size);
    } else memcpy(dest, &value, 8);
}
void ox_array_fill(Array *array, uint64_t value) {
    for (int64_t i = 0; i < array->length; i++) ox_array_set(array, i, value);
}
void ox_copy_array_data(Array *dest, Array *source) {
    if (dest->length != source->length) fail("Tamaños incompatibles en asignación de arreglo");
    memmove(dest->data, source->data, dest->length * dest->element->size);
}
int64_t ox_length(Array *array) { return array->length; }
Array *ox_clone_array(Array *array) {
    Array *result = ox_array_new(array->length, array->element);
    memcpy(result->data, array->data, array->length * array->element->size);
    return result;
}
Array *ox_reverse(Array *array) {
    size_t size = array->element->size;
    unsigned char *temp = allocate(size);
    for (int64_t i = 0; i < array->length / 2; i++) {
        void *a = ox_index(array, i), *b = ox_index(array, array->length - i - 1);
        memcpy(temp, a, size); memcpy(a, b, size); memcpy(b, temp, size);
    }
    return array;
}
static int equal_value(const void *a, const void *b, Type *type) {
    if (type->kind == 2) return *(const double *)a == *(const double *)b;
    if (type->kind == 5) return strcmp(*(char *const *)a, *(char *const *)b) == 0;
    if (type->kind == 6) {
        for (int64_t i = 0; i < type->length; i++) {
            if (!equal_value((const char *)a + i * type->child->size, (const char *)b + i * type->child->size, type->child)) return 0;
        }
        return 1;
    }
    return *(const uint64_t *)a == *(const uint64_t *)b;
}
int64_t ox_contains_array(Array *array, uint64_t value) {
    const void *search = array->element->kind == 6 ? (const void *)((Array *)value)->data : (const void *)&value;
    for (int64_t i = 0; i < array->length; i++) {
        if (equal_value(ox_index(array, i), search, array->element)) return 1;
    }
    return 0;
}
//argumentos f64 usan d0 por la ABI; el receptor permanece en x0
int64_t ox_contains_float(Array *array, double value) {
    uint64_t bits; memcpy(&bits, &value, 8); return ox_contains_array(array, bits);
}
Array *ox_split(const char *text, const char *separator) {
    size_t size = strlen(separator);
    if (!size) {
        Array *array = ox_array_new(ox_strlen(text) + 2, &string_type);
        char **values = (char **)array->data;
        values[0] = ox_string_copy("");
        const unsigned char *cursor = (const unsigned char *)text;
        int64_t index = 1;
        while (*cursor) values[index++] = ox_char_string(utf8_next(&cursor));
        values[index] = ox_string_copy("");
        return array;
    }
    int64_t count = 1;
    const char *cursor = text, *found;
    while ((found = strstr(cursor, separator))) { count++; cursor = found + size; }
    Array *array = ox_array_new(count, &string_type);
    char **values = (char **)array->data;
    cursor = text;
    for (int64_t i = 0; i < count; i++) {
        found = strstr(cursor, separator);
        size_t bytes = found ? (size_t)(found - cursor) : strlen(cursor);
        values[i] = allocate(bytes + 1); memcpy(values[i], cursor, bytes);
        cursor = found ? found + size : cursor + bytes;
    }
    return array;
}
Array *ox_chars(const char *text) {
    Array *array = ox_array_new(ox_strlen(text), &char_type);
    const unsigned char *cursor = (const unsigned char *)text;
    for (int64_t i = 0; i < array->length; i++) ((int64_t *)array->data)[i] = utf8_next(&cursor);
    return array;
}
int64_t ox_random(int64_t min, int64_t max) {
    if (min > max) fail("random requiere mínimo <= máximo");
    uint64_t bits = ((uint64_t)(unsigned)rand() << 32) | (unsigned)rand();
    return min + bits % (uint64_t)(max - min + 1);
}
static void print_value(FILE *out, uint64_t value, Type *type, int debug);
static void print_array(FILE *out, Array *array) {
    fputc('[', out);
    for (int64_t i = 0; i < array->length; i++) {
        if (i) fputs(", ", out);
        void *item = ox_index(array, i);
        if (array->element->kind == 6) {
            Array inner = {array->element->length, item, array->element->child};
            print_array(out, &inner);
        } else {
            uint64_t value; memcpy(&value, item, 8);
            print_value(out, value, array->element, 1);
        }
    }
    fputc(']', out);
}
static void print_value(FILE *out, uint64_t value, Type *type, int debug) {
    switch (type->kind) {
        case 1: fprintf(out, "%d", (int32_t)value); break;
        case 2: {
            double number; memcpy(&number, &value, 8);
            char buffer[64]; snprintf(buffer, sizeof(buffer), "%.15g", number);
            fputs(buffer, out);
            if (isfinite(number) && !strchr(buffer, '.') && !strchr(buffer, 'e')) fputs(".0", out);
            break;
        }
        case 3: fputs(value ? "true" : "false", out); break;
        case 4: { char text[5] = {0}; utf8_write(text, value); fputs(text, out); break; }
        case 5: if (debug) fputc('"', out); fputs((char *)value, out); if (debug) fputc('"', out); break;
        case 6: print_array(out, (Array *)value); break;
    }
}
void ox_print(uint64_t value, Type *type) { print_value(stdout, value, type, 0); }
void ox_print_text(const char *text) { fputs(text, stdout); }
char *ox_to_string(uint64_t value, Type *type) {
    char *buffer = NULL;
    size_t size = 0;
    FILE *out = open_memstream(&buffer, &size);
    if (!out) fail("No se pudo construir String");
    print_value(out, value, type, 0); fclose(out);
    char *result = ox_string_copy(buffer); free(buffer);
    return result;
}
