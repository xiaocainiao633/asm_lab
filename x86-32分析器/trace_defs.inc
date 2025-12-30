INST_MOV equ 1  
INST_ADD equ 2  
INST_SUB equ 3  
INST_FUNC_ENTRY equ 9  
INST_FUNC_EXIT equ 10  
INST_CALL_AFTER equ 12  
  
TRACE MACRO inst_type:REQ  
    pushad  
    pushfd  
    push ebp  
    mov eax, esp  
    add eax, 40  
    push eax  
    push edx  
    push ecx  
    push ebx  
    mov eax, [esp+48]  
    push eax  
    push offset $  
    push inst_type  
    call trace_record_entry  
    add esp, 32  
    popfd  
    popad  
ENDM  
  
TRACE_FUNC_ENTRY MACRO  
    TRACE INST_FUNC_ENTRY  
ENDM  
  
TRACE_FUNC_EXIT MACRO  
    TRACE INST_FUNC_EXIT  
ENDM  
  
TRACE_CALL_AFTER MACRO  
    TRACE INST_CALL_AFTER  
ENDM 
