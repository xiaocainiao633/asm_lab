; trace_buffer.asm - 轨迹缓冲区管理模块（修复版）

.386
.model flat, c
option casemap:none

include D:\masm32\include\windows.inc

.data
    ; 指令类型枚举
    INST_MOV equ 1
    INST_ADD equ 2
    INST_SUB equ 3
    INST_CALL equ 4
    INST_RET equ 5
    INST_JMP equ 6
    INST_JZ equ 7
    INST_JNZ equ 8
    
    MAX_TRACE_ENTRIES equ 10000     ; 最大记录条数（先用小一点的值测试）
    TRACE_ENTRY_SIZE equ 36         ; 每条记录大小（9个DWORD）
    
    ; 轨迹缓冲区
    trace_buffer db MAX_TRACE_ENTRIES * TRACE_ENTRY_SIZE dup(0)
    
    ; 当前状态
    current_entry_count dd 0
    buffer_full dd 0

.code

; 记录轨迹条目
; 参数通过栈传递: 指令类型, EIP, 寄存器快照
; 调用方式: 先 pushad 保存寄存器，再调用此函数
PUBLIC trace_record_entry
trace_record_entry PROC inst_type:DWORD, eip_val:DWORD, \
                        saved_eax:DWORD, saved_ebx:DWORD, saved_ecx:DWORD, \
                        saved_edx:DWORD, saved_esp:DWORD, saved_ebp:DWORD
    push edi
    push eax
    push ebx
    push ecx
    push edx
    
    ; 检查缓冲区是否已满
    cmp buffer_full, 1
    je skip_recording
    
    ; 检查是否达到最大记录数
    mov eax, current_entry_count
    cmp eax, MAX_TRACE_ENTRIES
    jae set_buffer_full
    
    ; 计算当前条目的偏移: offset = count * TRACE_ENTRY_SIZE
    mov ecx, TRACE_ENTRY_SIZE
    mul ecx
    lea edi, trace_buffer
    add edi, eax
    
    ; 记录指令序号
    mov eax, current_entry_count
    mov [edi], eax
    
    ; 记录EIP
    mov eax, eip_val
    mov [edi+4], eax
    
    ; 记录指令类型
    mov eax, inst_type
    mov [edi+8], eax
    
    ; 记录寄存器状态
    mov eax, saved_eax
    mov [edi+12], eax
    
    mov eax, saved_ebx
    mov [edi+16], eax
    
    mov eax, saved_ecx
    mov [edi+20], eax
    
    mov eax, saved_edx
    mov [edi+24], eax
    
    mov eax, saved_esp
    mov [edi+28], eax
    
    mov eax, saved_ebp
    mov [edi+32], eax
    
    ; 增加记录计数
    inc current_entry_count
    jmp done
    
set_buffer_full:
    mov buffer_full, 1
    
skip_recording:
done:
    pop edx
    pop ecx
    pop ebx
    pop eax
    pop edi
    ret
trace_record_entry ENDP

; 获取轨迹数据
; 返回: EAX = 轨迹条目数, EDX = 缓冲区地址
PUBLIC get_trace_data
get_trace_data PROC
    mov eax, current_entry_count
    lea edx, trace_buffer
    ret
get_trace_data ENDP

; 检查缓冲区是否已满
PUBLIC is_buffer_full
is_buffer_full PROC
    mov eax, buffer_full
    ret
is_buffer_full ENDP

END
