; test_nested.asm - 嵌套函数调用示例
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

; 函数A：返回5
FuncA proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    mov eax, 5
    TRACE INST_MOV
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
FuncA endp

; 函数B：调用FuncA，然后加10
FuncB proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call FuncA
    TRACE_CALL_AFTER
    
    add eax, 10
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
FuncB endp

; 函数C：调用FuncB，然后乘2
FuncC proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call FuncB
    TRACE_CALL_AFTER
    
    mov ebx, 2
    TRACE INST_MOV
    
    ; EAX = EAX * 2 (使用加法实现)
    add eax, eax
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
FuncC endp

start:
    call FuncC
    TRACE_CALL_AFTER
    
    call write_trace_file
    
    push 0
    call ExitProcess

end start
