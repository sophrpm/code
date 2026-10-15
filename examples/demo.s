// OxigenNative: AST -> AArch64
.section .rodata
.L_str_5:
    .byte 79,120,105,103,101,110,78,97,116,105,118,101,32,101,110,32,65,82,77,54,52,0
.L_str_6:
    .byte 70,105,98,111,110,97,99,99,105,40,49,48,41,58,32,0
    .balign 8
.L_type_7:
    .quad 1, 8, 0, 0
.L_str_8:
    .byte 0
    .balign 8
.L_type_9:
    .quad 6, 24, .L_type_7, 3
.L_str_10:
    .byte 77,97,116,114,105,122,58,32,0
    .balign 8
.L_type_11:
    .quad 6, 48, .L_type_9, 2
.L_str_12:
    .byte 0
.L_str_13:
    .byte 83,108,105,99,101,58,32,0
    .balign 8
.L_type_14:
    .quad 6, 8, .L_type_7, 0
.L_str_15:
    .byte 0
.L_str_16:
    .byte 72,111,108,97,32,77,117,110,100,111,0
    .balign 8
.L_type_17:
    .quad 5, 8, 0, 0
.L_str_18:
    .byte 77,117,110,100,111,0
.L_str_19:
    .byte 65,82,77,54,52,0
.L_str_20:
    .byte 0
.L_str_21:
    .byte 0
.L_str_22:
    .byte 32,0
.L_str_23:
    .byte 80,97,108,97,98,114,97,115,58,32,0
    .balign 8
.L_type_24:
    .quad 6, 8, .L_type_17, 0
.L_str_25:
    .byte 0
.L_str_26:
    .byte 68,105,118,105,115,105,195,179,110,58,32,0
    .balign 8
.L_type_27:
    .quad 2, 8, 0, 0
.L_str_28:
    .byte 0
.data
.text
.global main
.balign 4
// función fibonacci: guardar frame pointer y retorno
ox_fn_fibonacci:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    movz x9, #16
    // reservar locales, tamaño alineado a 16 bytes
    sub sp, sp, x9
    movz x9, #8
    sub x9, x29, x9
    str x0, [x9]
    movz x9, #8
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    movz x0, #2
    ldr x1, [sp], #16
    cmp x1, x0
    cset x0, lt
    cbz x0, .L_else_2
    movz x9, #8
    sub x0, x29, x9
    ldr x0, [x0]
    b .L_return_1
    b .L_endif_3
.L_else_2:
.L_endif_3:
    movz x9, #8
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    movz x0, #1
    ldr x1, [sp], #16
    sub w0, w1, w0
    sxtw x0, w0
    str x0, [sp, #-16]!
    movz x9, #0
    sub sp, sp, x9
    movz x9, #0
    ldr x0, [sp, x9]
    bl ox_fn_fibonacci
    movz x9, #16
    add sp, sp, x9
    str x0, [sp, #-16]!
    movz x9, #8
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    movz x0, #2
    ldr x1, [sp], #16
    sub w0, w1, w0
    sxtw x0, w0
    str x0, [sp, #-16]!
    movz x9, #0
    sub sp, sp, x9
    movz x9, #0
    ldr x0, [sp, x9]
    bl ox_fn_fibonacci
    movz x9, #16
    add sp, sp, x9
    ldr x1, [sp], #16
    add w0, w1, w0
    sxtw x0, w0
    b .L_return_1
    mov x0, #0
.L_return_1:
    // restaurar el frame y retornar al llamador
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret
// función main: guardar frame pointer y retorno
main:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    movz x9, #32
    // reservar locales, tamaño alineado a 16 bytes
    sub sp, sp, x9
    bl ox_init
    adrp x0, .L_str_5
    add x0, x0, :lo12:.L_str_5
    bl ox_print_text
    mov w0, #10
    bl putchar
    movz x0, #10
    str x0, [sp, #-16]!
    movz x9, #0
    sub sp, sp, x9
    movz x9, #0
    ldr x0, [sp, x9]
    bl ox_fn_fibonacci
    movz x9, #16
    add sp, sp, x9
    str x0, [sp, #-16]!
    adrp x0, .L_str_6
    add x0, x0, :lo12:.L_str_6
    bl ox_print_text
    movz x9, #0
    ldr x0, [sp, x9]
    adrp x1, .L_type_7
    add x1, x1, :lo12:.L_type_7
    bl ox_print
    adrp x0, .L_str_8
    add x0, x0, :lo12:.L_str_8
    bl ox_print_text
    movz x9, #16
    add sp, sp, x9
    mov w0, #10
    bl putchar
    movz x0, #2
    adrp x1, .L_type_9
    add x1, x1, :lo12:.L_type_9
    bl ox_array_new
    str x0, [sp, #-16]!
    movz x0, #3
    adrp x1, .L_type_7
    add x1, x1, :lo12:.L_type_7
    bl ox_array_new
    str x0, [sp, #-16]!
    movz x0, #1
    mov x2, x0
    movz x1, #0
    ldr x0, [sp]
    bl ox_array_set
    movz x0, #2
    mov x2, x0
    movz x1, #1
    ldr x0, [sp]
    bl ox_array_set
    movz x0, #3
    mov x2, x0
    movz x1, #2
    ldr x0, [sp]
    bl ox_array_set
    ldr x0, [sp], #16
    mov x2, x0
    movz x1, #0
    ldr x0, [sp]
    bl ox_array_set
    movz x0, #3
    adrp x1, .L_type_7
    add x1, x1, :lo12:.L_type_7
    bl ox_array_new
    str x0, [sp, #-16]!
    movz x0, #4
    mov x2, x0
    movz x1, #0
    ldr x0, [sp]
    bl ox_array_set
    movz x0, #5
    mov x2, x0
    movz x1, #1
    ldr x0, [sp]
    bl ox_array_set
    movz x0, #6
    mov x2, x0
    movz x1, #2
    ldr x0, [sp]
    bl ox_array_set
    ldr x0, [sp], #16
    mov x2, x0
    movz x1, #1
    ldr x0, [sp]
    bl ox_array_set
    ldr x0, [sp], #16
    str x0, [sp, #-16]!
    movz x9, #8
    sub x0, x29, x9
    ldr x1, [sp], #16
    str x1, [x0]
    movz x9, #8
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    movz x0, #1
    mov x1, x0
    ldr x0, [sp], #16
    bl ox_subarray
    str x0, [sp, #-16]!
    movz x0, #2
    mov x1, x0
    ldr x0, [sp], #16
    bl ox_index
    str x0, [sp, #-16]!
    movz x0, #7
    mov x1, x0
    ldr x0, [sp], #16
    str x1, [x0]
    movz x9, #8
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    adrp x0, .L_str_10
    add x0, x0, :lo12:.L_str_10
    bl ox_print_text
    movz x9, #0
    ldr x0, [sp, x9]
    adrp x1, .L_type_11
    add x1, x1, :lo12:.L_type_11
    bl ox_print
    adrp x0, .L_str_12
    add x0, x0, :lo12:.L_str_12
    bl ox_print_text
    movz x9, #16
    add sp, sp, x9
    mov w0, #10
    bl putchar
    movz x9, #8
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    movz x0, #1
    mov x1, x0
    ldr x0, [sp], #16
    bl ox_subarray
    str x0, [sp, #-16]!
    movz x0, #0
    str x0, [sp, #-16]!
    movz x0, #2
    str x0, [sp, #-16]!
    movz x9, #0
    sub sp, sp, x9
    movz x9, #32
    ldr x0, [sp, x9]
    movz x9, #16
    ldr x1, [sp, x9]
    movz x9, #0
    ldr x2, [sp, x9]
    bl ox_slice
    movz x9, #48
    add sp, sp, x9
    str x0, [sp, #-16]!
    movz x9, #16
    sub x0, x29, x9
    ldr x1, [sp], #16
    str x1, [x0]
    movz x9, #16
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    adrp x0, .L_str_13
    add x0, x0, :lo12:.L_str_13
    bl ox_print_text
    movz x9, #0
    ldr x0, [sp, x9]
    adrp x1, .L_type_14
    add x1, x1, :lo12:.L_type_14
    bl ox_print
    adrp x0, .L_str_15
    add x0, x0, :lo12:.L_str_15
    bl ox_print_text
    movz x9, #16
    add sp, sp, x9
    mov w0, #10
    bl putchar
    adrp x0, .L_str_16
    add x0, x0, :lo12:.L_str_16
    bl ox_string_copy
    adrp x1, .L_type_17
    add x1, x1, :lo12:.L_type_17
    bl ox_to_string
    str x0, [sp, #-16]!
    movz x9, #24
    sub x0, x29, x9
    ldr x1, [sp], #16
    str x1, [x0]
    movz x9, #24
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    adrp x0, .L_str_18
    add x0, x0, :lo12:.L_str_18
    bl ox_string_copy
    str x0, [sp, #-16]!
    adrp x0, .L_str_19
    add x0, x0, :lo12:.L_str_19
    bl ox_string_copy
    str x0, [sp, #-16]!
    movz x9, #0
    sub sp, sp, x9
    movz x9, #32
    ldr x0, [sp, x9]
    movz x9, #16
    ldr x1, [sp, x9]
    movz x9, #0
    ldr x2, [sp, x9]
    bl ox_replace
    movz x9, #48
    add sp, sp, x9
    str x0, [sp, #-16]!
    adrp x0, .L_str_20
    add x0, x0, :lo12:.L_str_20
    bl ox_print_text
    movz x9, #0
    ldr x0, [sp, x9]
    adrp x1, .L_type_17
    add x1, x1, :lo12:.L_type_17
    bl ox_print
    adrp x0, .L_str_21
    add x0, x0, :lo12:.L_str_21
    bl ox_print_text
    movz x9, #16
    add sp, sp, x9
    mov w0, #10
    bl putchar
    movz x9, #24
    sub x0, x29, x9
    ldr x0, [x0]
    str x0, [sp, #-16]!
    adrp x0, .L_str_22
    add x0, x0, :lo12:.L_str_22
    bl ox_string_copy
    str x0, [sp, #-16]!
    movz x9, #0
    sub sp, sp, x9
    movz x9, #16
    ldr x0, [sp, x9]
    movz x9, #0
    ldr x1, [sp, x9]
    bl ox_split
    movz x9, #32
    add sp, sp, x9
    str x0, [sp, #-16]!
    adrp x0, .L_str_23
    add x0, x0, :lo12:.L_str_23
    bl ox_print_text
    movz x9, #0
    ldr x0, [sp, x9]
    adrp x1, .L_type_24
    add x1, x1, :lo12:.L_type_24
    bl ox_print
    adrp x0, .L_str_25
    add x0, x0, :lo12:.L_str_25
    bl ox_print_text
    movz x9, #16
    add sp, sp, x9
    mov w0, #10
    bl putchar
    movz x0, #7
    scvtf d0, w0
    str d0, [sp, #-16]!
    movz x9, #32
    sub x0, x29, x9
    ldr d1, [sp], #16
    str d1, [x0]
    movz x9, #32
    sub x0, x29, x9
    ldr d0, [x0]
    str d0, [sp, #-16]!
    movz x0, #2
    scvtf d0, w0
    ldr d1, [sp], #16
    fcmp d0, #0.0
    b.eq ox_zero
    fdiv d0, d1, d0
    str d0, [sp, #-16]!
    adrp x0, .L_str_26
    add x0, x0, :lo12:.L_str_26
    bl ox_print_text
    movz x9, #0
    ldr x0, [sp, x9]
    adrp x1, .L_type_27
    add x1, x1, :lo12:.L_type_27
    bl ox_print
    adrp x0, .L_str_28
    add x0, x0, :lo12:.L_str_28
    bl ox_print_text
    movz x9, #16
    add sp, sp, x9
    mov w0, #10
    bl putchar
    mov x0, #0
.L_return_4:
    // restaurar el frame y retornar al llamador
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret
.section .note.GNU-stack,"",@progbits
