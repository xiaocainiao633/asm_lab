; test_extreme.asm - 极端测试用例
; 测试深度嵌套、递归和插桩透明性

.386
.model flat, stdcall
option casemap:none

include D:\masm32\include\windows.inc
include D:\masm32\include\kernel32.inc
includelib D:\masm32\lib\kernel32.lib

extern C trace_record_entry:proc
extern C write_trace_file:proc

include trace_defs.inc

.data
    msg_start db "========================================", 0Dh, 0Ah
              db "极端测试用例 - 深度嵌套与递归", 0Dh, 0Ah
              db "========================================", 0Dh, 0Ah, 0
    msg_done db 0Dh, 0Ah, "测试完成，轨迹已记录", 0Dh, 0Ah, 0
    bytes_written dd 0

.code

; ============================================================================
; 测试 1: 深度嵌套调用（10层）
; ============================================================================

Level10 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    mov eax, 10
    TRACE INST_MOV
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level10 endp

Level9 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level10
    TRACE_CALL_AFTER
    
    add eax, 9
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level9 endp

Level8 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level9
    TRACE_CALL_AFTER
    
    add eax, 8
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level8 endp

Level7 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level8
    TRACE_CALL_AFTER
    
    add eax, 7
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level7 endp

Level6 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level7
    TRACE_CALL_AFTER
    
    add eax, 6
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level6 endp

Level5 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level6
    TRACE_CALL_AFTER
    
    add eax, 5
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level5 endp

Level4 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level5
    TRACE_CALL_AFTER
    
    add eax, 4
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level4 endp

Level3 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level4
    TRACE_CALL_AFTER
    
    add eax, 3
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level3 endp

Level2 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level3
    TRACE_CALL_AFTER
    
    add eax, 2
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level2 endp

Level1 proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    call Level2
    TRACE_CALL_AFTER
    
    add eax, 1
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Level1 endp

; ============================================================================
; 测试 2: 递归函数（阶乘）
; 计算 n! (限制 n <= 5 以避免轨迹过长)
; 参数: [ebp+8] = n
; 返回: EAX = n!
; ============================================================================
Factorial proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    ; 获取参数 n
    mov eax, [ebp+8]
    TRACE INST_MOV
    
    ; 基础情况: if (n <= 1) return 1
    cmp eax, 1
    jg recursive_case
    
    ; 返回 1
    mov eax, 1
    TRACE INST_MOV
    jmp factorial_done
    
recursive_case:
    ; 保存 n
    push eax
    
    ; 递归调用: factorial(n-1)
    sub eax, 1
    TRACE INST_SUB
    
    push eax
    call Factorial
    TRACE_CALL_AFTER
    add esp, 4
    
    ; 恢复 n
    pop ebx
    
    ; 计算 n * factorial(n-1)
    ; 注意：这里简化处理，实际应该用 mul
    ; 为了简单，我们只测试小数字
    push ecx
    mov ecx, ebx
    xor ebx, ebx
multiply_loop:
    cmp ecx, 0
    je multiply_done
    add ebx, eax
    dec ecx
    jmp multiply_loop
multiply_done:
    mov eax, ebx
    pop ecx
    TRACE INST_ADD              ; 标记乘法完成
    
factorial_done:
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
Factorial endp

; ============================================================================
; 测试 3: 插桩透明性验证
; 验证插桩前后寄存器和栈状态完全一致
; ============================================================================
TransparencyTest proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    ; 设置特定的寄存器值
    mov eax, 12345678h
    mov ebx, 87654321h
    mov ecx, 0ABCDEFh
    mov edx, 0FEDCBAh
    TRACE INST_MOV
    
    ; 插桩后，这些值应该保持不变
    ; 验证 EAX
    cmp eax, 12345678h
    jne transparency_failed
    
    ; 验证 EBX
    cmp ebx, 87654321h
    jne transparency_failed
    
    ; 验证 ECX
    cmp ecx, 0ABCDEFh
    jne transparency_failed
    
    ; 验证 EDX
    cmp edx, 0FEDCBAh
    jne transparency_failed
    
    ; 透明性测试通过
    mov eax, 1
    TRACE INST_MOV
    jmp transparency_done
    
transparency_failed:
    ; 透明性测试失败
    mov eax, 0
    TRACE INST_MOV
    
transparency_done:
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
TransparencyTest endp

; ============================================================================
; 主测试函数
; ============================================================================
MainTest proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    ; 测试 1: 深度嵌套（10层）
    call Level1
    TRACE_CALL_AFTER
    ; 结果应该是 10+9+8+7+6+5+4+3+2+1 = 55
    
    ; 测试 2: 递归（计算 4!）
    push 4
    call Factorial
    TRACE_CALL_AFTER
    add esp, 4
    ; 结果应该是 24
    
    ; 测试 3: 插桩透明性
    call TransparencyTest
    TRACE_CALL_AFTER
    ; 结果应该是 1（成功）
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
MainTest endp

; ============================================================================
; 程序入口
; ============================================================================
start:
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    push eax
    invoke WriteFile, eax, offset msg_start, sizeof msg_start, offset bytes_written, 0
    
    call MainTest
    TRACE_CALL_AFTER
    
    call write_trace_file
    
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    invoke WriteFile, eax, offset msg_done, sizeof msg_done, offset bytes_written, 0
    
    push 0
    call ExitProcess

end start
