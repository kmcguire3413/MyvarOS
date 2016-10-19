#include "main.h"
#include "sedna/common.h"

static uint8_t *alloc_null_terminated_string(void *offset, uintptr_t size) {
    uint8_t *out;

    if (size == 0) {
        // The most safe action, but not that efficient.
        out = (uint8_t*)kmalloc(1);
        *out = 0;
        return out;
    }

    if (*((uint8_t*)offset + size - 1) == 0) {
        out = (uint8_t*)kmalloc(size);
        if (out == 0) {
            panic("alloc_null_terminated_string OOM");
        }
        memcpy(out, offset, size);
    } else {
        out = (uint8_t*)kmalloc(size + 1);
        if (out == 0) {
            panic("alloc_null_terminated_string OOM");
        }
        memcpy(out, offset, size);
        out[size] = 0;
    }

    return out;
}

SEDNAMODULE* sedna_load_module(uintptr_t address)
{
    SEDNAMODULE     *mod;
    SEDNAMETHOD     *meth;
    int32_t         sz;
    int32_t         index;
    uint32_t        offset;
    int32_t         x;

    mod = kmalloc(sizeof(SEDNAMODULE));

    sz = READ_SEDNA_INT(address, 0);
    offset += sizeof(SEDNA_INT);

    //kprintf("scope-address: %x scope-length: %x", (uintptr_t)address + offset, sz);
    mod->scope = alloc_null_terminated_string((uint8_t*)address + offset, sz);
    offset += sz;

    //kprintf(" scope: %s\n", mod->scope);


    int32_t total_imports = READ_SEDNA_INT(address, offset);
    offset += sizeof(SEDNA_INT);

    //kprintf("total-imports: %x\n", total_imports);

    mod->import_cnt = total_imports;
    mod->import = (uint8_t**)kmalloc(sizeof(uint8_t*) * mod->import_cnt);

    for(index = 0; index < total_imports; index++)
    {   
        sz = READ_SEDNA_INT(address, offset);
        offset += sizeof(SEDNA_INT);
        mod->import[index] = alloc_null_terminated_string((uint8_t*)address + offset, sz);
        offset += sz;

        //kprintf("import-address: %x import-size: %x import: %s\n", (uintptr_t)address + offset, sz, mod->import[index]);
    }

    char *s;
    char buf[20];

    int32_t total_types = READ_SEDNA_INT(address, offset);
    offset += sizeof(SEDNA_INT);

    mod->type_cnt = total_types;
    mod->type = (uint8_t**)kmalloc(sizeof(uint8_t*) * mod->type_cnt);
    mod->type_base = (uint8_t**)kmalloc(sizeof(uint8_t*) * mod->type_cnt);

    for(index = 0; index < total_types; index++)
    {   
        sz = READ_SEDNA_INT(address, offset);
        offset += sizeof(SEDNA_INT);
        mod->type[index] = alloc_null_terminated_string((uint8_t*)address + offset, sz);
        offset += sz;

        sz = READ_SEDNA_INT(address, offset);
        offset += sizeof(SEDNA_INT);
        mod->type_base[index] = alloc_null_terminated_string((uint8_t*)address + offset, sz);
        offset += sz;

        //kprintf("type: %s base: %s\n", mod->type[index], mod->type_base[index]);
    }


    int32_t total_fns = READ_SEDNA_INT(address, offset);
    offset += sizeof(SEDNA_INT);

    mod->method_cnt = total_fns;
    mod->method = (SEDNAMETHOD*)kmalloc(sizeof(SEDNAMETHOD) * mod->method_cnt);

    for(index = 0; index < total_fns; index++)
    {   
        // Method name.
        sz = READ_SEDNA_INT(address, offset);
        offset += sizeof(SEDNA_INT);
        mod->method[index].name = alloc_null_terminated_string((uint8_t*)address + offset, sz);
        offset += sz;

        int32_t total_para = READ_SEDNA_INT(address, offset);
        offset += sizeof(SEDNA_INT);

        mod->method[index].param_cnt = total_para;
        mod->method[index].param_type = (uint8_t**)kmalloc(sizeof(uint8_t*) * mod->method[index].param_cnt);

        //kprintf("method: %s parameter-count: %x\n", mod->method[index].name, mod->method[index].param_cnt);

        for(x = 0; x < total_para; x++)
        {
            sz = READ_SEDNA_INT(address, offset);
            offset += sizeof(SEDNA_INT);
            mod->method[index].param_type[x] = alloc_null_terminated_string((uint8_t*)address + offset, sz);
            //kprintf("   method-parameter-type: %s\n", mod->method[index].param_type[x]);
            offset += sz;
        }
        
        // This was added to keep from interpreting the bytecode
        // at this very moment.
        SEDNA_INT bytecode_sz = READ_SEDNA_INT(address, offset);
        offset += sizeof(SEDNA_INT);

        SEDNA_INT op_cnt = READ_SEDNA_INT(address, offset);
        offset += sizeof(SEDNA_INT);

        //kprintf("   op-count: %x bytecode-sz: %x\n", op_cnt, bytecode_sz);

        mod->method[index].op_cnt = op_cnt;
        mod->method[index].bytecode_sz = bytecode_sz;
        mod->method[index].bytecode = kmalloc(bytecode_sz);
        memcpy(mod->method[index].bytecode, (uint8_t*)(address + offset), bytecode_sz);
    }

    return mod;
}