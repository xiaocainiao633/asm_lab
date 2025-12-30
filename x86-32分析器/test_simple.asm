; test_simple.asm - 简单示例：两个数相加
.386
.model flat, stdcall
option casemap:none

include D:\masm32\include\windows.inc
include D:\masm32\include\kernel32.inc
includelib D:\masm32\lib\kernel32.lib

extern C trace_record_entry:proc
extern C write_trace_file:proc

include trace_defs.inc

.code

; 简单的加法函数
AddTwo proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    mov eax, 10
    TRACE INST_MOV
    
    add eax, 20
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
AddTwo endp

start:
    call AddTwo
    TRACE_CALL_AFTER
    
    call write_trace_file
    
    push 0
    call ExitProcess

end start
