#include "sedna/common.h"
#include "kernel.h"

static SEDNAVM 		**vm = 0;
static uint16_t     vmused = 0;
static uint16_t	    vmlimit = 0;

void sedna_vm_list_realloc(uint16_t newcount) {
	SEDNAVM *tmp = (SEDNAVM**)kmalloc(sizeof(SEDNAVM*) * newcount)

	memset(tmp, 0, sizeof(SEDNAVM*) * newcount);

	if (vmlimit > 0) {
		memcpy(tmp, vm, sizeof(SEDNAVM*) * vmlimit);
	}

	vm = tmp;
}

void sedna_vm_init(SEDNAVMHANDLE vmi) {
	
}

SEDNAVMHANDLE sedna_vm_create(SEDNAMODULE *mod) {
	uint16_t vmi;

	if (vmused + 1 >= vmlimit) {
		if (vmlimit * 2 > 0xffff) {
			panic("The SEDNA VM limit of 0xffff has been reached.")
		}

		sedna_vm_list_realloc(vmlimit * 2);
	}

	for (vmi = 0; vmi < vmlimit; ++vmi) {
		if (vm[vmi] == 0) {
			break;
		}
	}

	if (vmi == vmlimit) {
		panic("The SEDNA VM could not find a free slot. [bug]")
	}

	vm[vmi] = (SEDNAVM*)kmalloc(sizeof(SEDNAVM));

	memset(vm[vmi], 0, sizeof(SEDNAVM));

	sedna_vm_init((SEDNAVMHANDLE)vmi);

	return (SEDNAVMHANDLE)vmi;
}

uint8_t sedna_vm_execute(SEDNAVMHANDLE vmid, uint32_t opcnt) {

}
