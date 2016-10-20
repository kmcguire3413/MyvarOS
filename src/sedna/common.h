#ifndef KERNEL_SEDNA_COMMON_H
#define KERNEL_SEDNA_COMMON_H
#include <stdint.h>

#define READ_SEDNA_INT(base, byte_offset) *((int32_t*)(base + byte_offset))
typedef uint8_t SEDNA_OP_WORD;
typedef int32_t SEDNA_INT;

typedef struct {
    uint8_t             *name;
    uint16_t            param_cnt;
    uint8_t             **param_type;
    uint32_t            op_cnt;
    uint32_t            bytecode_sz;
    uint8_t             *bytecode;
} SEDNAMETHOD;

typedef struct {
    uint8_t             *scope;
    uint32_t            import_cnt;
    uint8_t             **import;
    uint32_t            type_cnt;
    uint8_t             **type;
    uint8_t             **type_base;
    uint32_t            method_cnt;
    SEDNAMETHOD         *method;
} SEDNAMODULE;

typedef struct {
    uintptr_t           *stack;
} SEDNAVM;

typedef uint16_t SEDNAVMHANDLE;

static uint8_t *alloc_null_terminated_string(void *offset, uintptr_t size);
SEDNAMODULE* sedna_load_module(uintptr_t address);
uint8_t sedna_vm_execute(SEDNAVMID vmid, uint32_t opcnt);
SEDNAVMID sedna_vm_create(SEDNAMODULE *mod);
#endif