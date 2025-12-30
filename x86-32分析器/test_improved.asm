; test_improved.asm - 使用改进插桩策略的测试程序
; 展示清晰的函数边界和调用关系

.386
.model flat, stdcall
option casemap:none

include D:\masm32\include\windows.inc
include D:\masm32\include\kernel32.inc
includelib D:\masm32\lib\kernel32.lib

; 外部函数声明
extern C trace_record_entry:proc
extern C write_trace_file:proc

; 包含插桩定义
include trace_defs.inc

.data
    msg_start db "========================================", 0Dh, 0Ah
              db "改进版插桩测试程序", 0Dh, 0Ah
              db "========================================", 0Dh, 0Ah, 0
    msg_done db 0Dh, 0Ah, "========================================", 0Dh, 0Ah
             db "程序执行完成，轨迹已记录", 0Dh, 0Ah
             db "运行 trace_analyzer.exe 查看分析结果", 0Dh, 0Ah
             db "========================================", 0Dh, 0Ah, 0
    bytes_written dd 0

.code

; ============================================================================
; 函数 1: 简单加法
; 参数: [ebp+8] = a, [ebp+12] = b
; 返回: EAX = a + b
; ============================================================================
AddNumbers proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY            ; 标记函数入口
    
    mov eax, [ebp+8]
    TRACE INST_MOV
    
    add eax, [ebp+12]
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT             ; 标记函数出口
    ret
AddNumbers endp

; ============================================================================
; 函数 2: 简单减法
; 参数: [ebp+8] = a, [ebp+12] = b
; 返回: EAX = a - b
; ============================================================================
SubNumbers proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    mov eax, [ebp+8]
    TRACE INST_MOV
    
    sub eax, [ebp+12]
    TRACE INST_SUB
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
SubNumbers endp

; ============================================================================
; 函数 3: 复合运算
; 计算: (a + b) - (c - d)
; 参数: [ebp+8]=a, [ebp+12]=b, [ebp+16]=c, [ebp+20]=d
; 返回: EAX = (a+b) - (c-d)
; ============================================================================
ComplexCalc proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    ; 计算 a + b
    push dword ptr [ebp+12]     ; b
    push dword ptr [ebp+8]      ; a
    call AddNumbers
    TRACE_CALL_AFTER            ; 标记 call 返回
    add esp, 8
    
    push eax                    ; 保存结果
    
    ; 计算 c - d
    push dword ptr [ebp+20]     ; d
    push dword ptr [ebp+16]     ; c
    call SubNumbers
    TRACE_CALL_AFTER
    add esp, 8
    
    ; 计算最终结果
    mov ebx, eax
    pop eax
    sub eax, ebx
    TRACE INST_SUB
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
ComplexCalc endp

; ============================================================================
; 函数 4: 主测试函数
; ============================================================================
TestFunction proc
    push ebp
    mov ebp, esp
    TRACE_FUNC_ENTRY
    
    ; 测试 1: AddNumbers(10, 20) = 30
    push 20
    push 10
    call AddNumbers
    TRACE_CALL_AFTER
    add esp, 8
    
    push eax                    ; 保存结果
    
    ; 测试 2: SubNumbers(100, 30) = 70
    push 30
    push 100
    call SubNumbers
    TRACE_CALL_AFTER
    add esp, 8
    
    ; 合并结果: 30 + 70 = 100
    pop ebx
    add eax, ebx
    TRACE INST_ADD
    
    push eax                    ; 保存结果
    
    ; 测试 3: ComplexCalc(10, 20, 50, 15)
    ;         = (10+20) - (50-15) = 30 - 35 = -5
    push 15
    push 50
    push 20
    push 10
    call ComplexCalc
    TRACE_CALL_AFTER
    add esp, 16
    
    ; 最终结果
    pop ebx
    add eax, ebx                ; 100 + (-5) = 95
    TRACE INST_ADD
    
    mov esp, ebp
    pop ebp
    TRACE_FUNC_EXIT
    ret
TestFunction endp

; ============================================================================
; 程序入口
; ============================================================================
start:
    ; 输出开始消息
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    push eax
    invoke WriteFile, eax, offset msg_start, sizeof msg_start, offset bytes_written, 0
    
    ; 调用主测试函数
    call TestFunction
    TRACE_CALL_AFTER
    
    ; 写入轨迹文件
    call write_trace_file
    
    ; 输出完成消息
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    invoke WriteFile, eax, offset msg_done, sizeof msg_done, offset bytes_written, 0
    
    ; 退出程序
    push 0
    call ExitProcess

end start
