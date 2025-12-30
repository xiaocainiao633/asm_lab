; trace_analyzer.asm - 增强版轨迹分析程序
; 功能：调用栈分析、CALL/RET 配对检测、ESP 异常检测

.386
.model flat, stdcall
option casemap:none

include D:\masm32\include\windows.inc
include D:\masm32\include\kernel32.inc
include D:\masm32\include\msvcrt.inc
includelib D:\masm32\lib\kernel32.lib
includelib D:\masm32\lib\msvcrt.lib

.data
    trace_file_name db "execution_trace.bin", 0
    
    ; 指令类型常量
    INST_MOV equ 1
    INST_ADD equ 2
    INST_SUB equ 3
    INST_CALL equ 4
    INST_RET equ 5
    INST_JMP equ 6
    INST_JZ equ 7
    INST_JNZ equ 8
    INST_FUNC_ENTRY equ 9
    INST_FUNC_EXIT equ 10
    INST_CALL_BEFORE equ 11
    INST_CALL_AFTER equ 12
    
    ; 指令类型名称
    inst_names dd offset mov_name, offset add_name, offset sub_name
               dd offset call_name, offset ret_name, offset jmp_name
               dd offset jz_name, offset jnz_name, offset func_entry_name
               dd offset func_exit_name, offset call_before_name, offset call_after_name
    
    mov_name db "MOV", 0
    add_name db "ADD", 0
    sub_name db "SUB", 0
    call_name db "CALL", 0
    ret_name db "RET", 0
    jmp_name db "JMP", 0
    jz_name db "JZ", 0
    jnz_name db "JNZ", 0
    func_entry_name db "FUNC_ENTRY", 0
    func_exit_name db "FUNC_EXIT", 0
    call_before_name db "CALL_BEFORE", 0
    call_after_name db "CALL_AFTER", 0
    unknown_name db "???", 0
    
    ; 输出格式
    header_fmt db "╔════════════════════════════════════════════════════════════╗", 0Dh, 0Ah
               db "║          执行轨迹分析 - 调用栈可视化                      ║", 0Dh, 0Ah
               db "╚════════════════════════════════════════════════════════════╝", 0Dh, 0Ah, 0
    
    ; 带缩进的条目格式
    entry_fmt db 0Dh, 0Ah, "#%-4d %s%s", 0
    entry_detail db " EIP=%08X", 0Dh, 0Ah, 0
    
    ; 寄存器格式
    reg_fmt db "%s      EAX=%08X  EBX=%08X  ECX=%08X  EDX=%08X", 0Dh, 0Ah, 0
    
    ; 栈格式（正常）
    stack_fmt db "%s      ESP=%08X  EBP=%08X", 0
    
    ; 栈格式（有变化）
    stack_change_fmt db " [ESP: %08X -> %08X, 变化: %d]", 0Dh, 0Ah, 0
    stack_no_change_fmt db 0Dh, 0Ah, 0
    
    ; CALL 特殊格式
    call_fmt db " -> 调用深度: %d", 0Dh, 0Ah, 0
    
    ; RET 特殊格式
    ret_fmt db " <- 返回到深度: %d", 0Dh, 0Ah, 0
    
    ; 警告信息
    warn_esp_jump db "%s      [警告] ESP 异常跳变: %d 字节", 0Dh, 0Ah, 0
    warn_ret_mismatch db "%s      [警告] RET 不匹配: 调用栈为空", 0Dh, 0Ah, 0
    warn_esp_mismatch db "%s      [警告] RET 后 ESP 不匹配: 期望 %08X, 实际 %08X", 0Dh, 0Ah, 0
    
    ; 摘要格式
    summary_header db 0Dh, 0Ah, "╔════════════════════════════════════════════════════════════╗", 0Dh, 0Ah
                   db "║                      分析摘要                              ║", 0Dh, 0Ah
                   db "╚════════════════════════════════════════════════════════════╝", 0Dh, 0Ah, 0
    
    summary_total db "总指令数:           %d", 0Dh, 0Ah, 0
    summary_calls db "CALL 指令数:        %d", 0Dh, 0Ah, 0
    summary_rets db "RET 指令数:         %d", 0Dh, 0Ah, 0
    summary_max_depth db "最大调用深度:       %d", 0Dh, 0Ah, 0
    summary_warnings db "警告数:             %d", 0Dh, 0Ah, 0
    summary_final_depth db "最终调用深度:       %d", 0
    summary_ok db " (正常)", 0Dh, 0Ah, 0
    summary_err db " (异常: 应为0)", 0Dh, 0Ah, 0
    
    ; 缩进字符串（每层2个空格）
    indent_str db "                                                  ", 0  ; 50个空格
    
    error_msg db "错误: 无法读取轨迹文件", 0Dh, 0Ah, 0

.data?
    file_handle dd ?
    bytes_read dd ?
    file_size dd ?
    trace_data dd ?
    entry_count dd ?
    
    ; 调用栈（简单实现：只记录 ESP 值）
    MAX_CALL_DEPTH equ 100
    call_stack dd MAX_CALL_DEPTH dup(?)
    call_depth dd ?
    max_call_depth dd ?
    
    ; 统计信息
    call_count dd ?
    ret_count dd ?
    warning_count dd ?
    
    ; 前一条记录的 ESP
    prev_esp dd ?
    
    ; 临时缓冲区
    temp_buffer db 256 dup(?)

.code

start:
    ; 初始化
    mov call_depth, 0
    mov max_call_depth, 0
    mov call_count, 0
    mov ret_count, 0
    mov warning_count, 0
    mov prev_esp, 0
    
    ; 显示标题
    invoke crt_printf, offset header_fmt
    
    ; 读取轨迹文件
    call read_trace_file
    cmp eax, 0
    jne analyze_trace
    
    ; 错误处理
    invoke crt_printf, offset error_msg
    jmp exit_program
    
analyze_trace:
    ; 分析轨迹数据
    call analyze_trace_data
    
    ; 显示摘要
    call display_summary
    
exit_program:
    ; 释放内存
    cmp trace_data, 0
    je skip_free
    invoke GlobalFree, trace_data
skip_free:
    
    invoke ExitProcess, 0

; 读取轨迹文件（与原版相同）
read_trace_file PROC
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    invoke CreateFileA, offset trace_file_name, GENERIC_READ, FILE_SHARE_READ, \
                        0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0
    
    cmp eax, INVALID_HANDLE_VALUE
    je open_failed
    mov file_handle, eax
    
    invoke GetFileSize, file_handle, 0
    mov file_size, eax
    
    invoke GlobalAlloc, GMEM_FIXED, file_size
    cmp eax, 0
    je alloc_failed
    mov trace_data, eax
    
    invoke ReadFile, file_handle, trace_data, file_size, offset bytes_read, 0
    cmp eax, 0
    je read_failed
    
    invoke CloseHandle, file_handle
    
    mov esi, trace_data
    cmp dword ptr [esi], 43415254h
    jne invalid_format
    cmp dword ptr [esi+4], 31303045h
    jne invalid_format
    
    mov eax, file_size
    sub eax, 8
    mov ecx, 36
    xor edx, edx
    div ecx
    mov entry_count, eax
    
    add trace_data, 8
    
    mov eax, 1
    jmp done
    
open_failed:
alloc_failed:
read_failed:
invalid_format:
    xor eax, eax
    
done:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret
read_trace_file ENDP

; 获取缩进字符串
; 输入: EAX = 深度
; 输出: EAX = 缩进字符串地址
get_indent PROC
    push ebp
    mov ebp, esp
    push ebx
    
    ; 限制最大深度
    cmp eax, 25
    jbe depth_ok
    mov eax, 25
depth_ok:
    
    ; 每层2个空格
    shl eax, 1
    
    ; 计算偏移
    lea ebx, indent_str
    add ebx, eax
    
    ; 临时终止符
    mov byte ptr [ebx], 0
    
    lea eax, indent_str
    
    pop ebx
    pop ebp
    ret
get_indent ENDP

; 恢复缩进字符串
restore_indent PROC
    push ebp
    mov ebp, esp
    push edi
    push ecx
    
    ; 恢复所有空格
    lea edi, indent_str
    mov ecx, 50
    mov al, ' '
    rep stosb
    mov byte ptr [edi], 0
    
    pop ecx
    pop edi
    pop ebp
    ret
restore_indent ENDP

; 分析轨迹数据
analyze_trace_data PROC
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    mov esi, trace_data
    xor ecx, ecx                    ; 条目计数器
    
analyze_loop:
    cmp ecx, entry_count
    jae done
    
    push ecx
    push esi
    
    ; 读取当前条目
    mov eax, [esi]                  ; instruction_number
    mov ebx, [esi+4]                ; eip
    mov edx, [esi+8]                ; instruction_type
    
    ; 根据指令类型处理
    cmp edx, INST_FUNC_ENTRY
    je handle_func_entry
    cmp edx, INST_FUNC_EXIT
    je handle_func_exit
    cmp edx, INST_CALL
    je handle_call
    cmp edx, INST_RET
    je handle_ret
    cmp edx, INST_CALL_AFTER
    je handle_call_after
    jmp handle_normal
    
handle_func_entry:
    ; 函数入口：压入调用栈
    mov edi, call_depth
    cmp edi, MAX_CALL_DEPTH
    jae call_overflow
    
    ; 保存当前 ESP
    mov eax, [esi+28]
    mov [call_stack + edi*4], eax
    
    ; 增加深度
    inc call_depth
    mov edi, call_depth
    
    ; 更新最大深度
    cmp edi, max_call_depth
    jbe skip_max_update1
    mov max_call_depth, edi
skip_max_update1:
    
    ; 增加 CALL 计数
    inc call_count
    
    ; 显示函数入口
    push esi
    call display_func_entry
    jmp next_entry
    
handle_func_exit:
    ; 函数出口：从调用栈弹出
    mov edi, call_depth
    cmp edi, 0
    je ret_underflow
    
    ; 减少深度
    dec call_depth
    
    ; 检查 ESP 是否匹配
    dec edi
    mov eax, [call_stack + edi*4]
    mov ebx, [esi+28]
    
    ; 函数出口时，ESP 应该恢复到入口时的值
    cmp ebx, eax
    je esp_match_exit
    
    ; ESP 不匹配，发出警告
    push ebx
    push eax
    call display_esp_mismatch_warning
    add esp, 8
    inc warning_count
    
esp_match_exit:
    ; 增加 RET 计数
    inc ret_count
    
    ; 显示函数出口
    push esi
    call display_func_exit
    jmp next_entry
    
handle_call_after:
    ; CALL 返回后：仅显示，不影响调用栈
    push esi
    call display_call_after
    jmp next_entry
    
handle_call:
    ; CALL 指令：压入调用栈
    mov edi, call_depth
    cmp edi, MAX_CALL_DEPTH
    jae call_overflow
    
    ; 保存当前 ESP
    mov eax, [esi+28]
    mov [call_stack + edi*4], eax
    
    ; 增加深度
    inc call_depth
    mov edi, call_depth
    
    ; 更新最大深度
    cmp edi, max_call_depth
    jbe skip_max_update2
    mov max_call_depth, edi
skip_max_update2:
    
    ; 增加 CALL 计数
    inc call_count
    
    ; 显示 CALL 指令
    push esi
    call display_call_entry
    jmp next_entry
    
call_overflow:
    ; 调用栈溢出（不应该发生）
    jmp handle_normal
    
handle_ret:
    ; RET 指令：从调用栈弹出
    mov edi, call_depth
    cmp edi, 0
    je ret_underflow
    
    ; 减少深度
    dec call_depth
    
    ; 检查 ESP 是否匹配
    dec edi
    mov eax, [call_stack + edi*4]
    mov ebx, [esi+28]
    
    ; ESP 应该恢复到 CALL 之前的值
    ; 注意：RET 会弹出返回地址，所以 ESP 应该比 CALL 时大4
    add eax, 4
    cmp ebx, eax
    je esp_match
    
    ; ESP 不匹配，发出警告
    push ebx
    push eax
    call display_esp_mismatch_warning
    add esp, 8
    inc warning_count
    
esp_match:
    ; 增加 RET 计数
    inc ret_count
    
    ; 显示 RET 指令
    push esi
    call display_ret_entry
    jmp next_entry
    
ret_underflow:
    ; RET 但调用栈为空
    call display_ret_mismatch_warning
    inc warning_count
    inc ret_count
    push esi
    call display_ret_entry
    jmp next_entry
    
handle_normal:
    ; 普通指令
    push esi
    call display_normal_entry
    
next_entry:
    ; 恢复缩进字符串
    call restore_indent
    
    pop esi
    pop ecx
    
    ; 保存当前 ESP
    mov eax, [esi+28]
    mov prev_esp, eax
    
    ; 下一个条目
    add esi, 36
    inc ecx
    jmp analyze_loop
    
done:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret
analyze_trace_data ENDP

; 显示函数入口
display_func_entry PROC
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    mov esi, [ebp+8]
    
    ; 获取缩进（使用当前深度-1）
    mov eax, call_depth
    dec eax
    call get_indent
    mov edi, eax
    
    ; 显示条目
    push offset func_entry_name
    push edi
    push dword ptr [esi]
    push offset entry_fmt
    call crt_printf
    add esp, 16
    
    push dword ptr [esi+4]
    push offset entry_detail
    call crt_printf
    add esp, 8
    
    push dword ptr [esi+24]
    push dword ptr [esi+20]
    push dword ptr [esi+16]
    push dword ptr [esi+12]
    push edi
    push offset reg_fmt
    call crt_printf
    add esp, 24
    
    push dword ptr [esi+32]
    push dword ptr [esi+28]
    push edi
    push offset stack_fmt
    call crt_printf
    add esp, 16
    
    push call_depth
    push offset call_fmt
    call crt_printf
    add esp, 8
    
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret 4
display_func_entry ENDP

; 显示函数出口
display_func_exit PROC
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    mov esi, [ebp+8]
    
    ; 获取缩进（使用返回后的深度）
    mov eax, call_depth
    call get_indent
    mov edi, eax
    
    push offset func_exit_name
    push edi
    push dword ptr [esi]
    push offset entry_fmt
    call crt_printf
    add esp, 16
    
    push dword ptr [esi+4]
    push offset entry_detail
    call crt_printf
    add esp, 8
    
    push dword ptr [esi+24]
    push dword ptr [esi+20]
    push dword ptr [esi+16]
    push dword ptr [esi+12]
    push edi
    push offset reg_fmt
    call crt_printf
    add esp, 24
    
    push dword ptr [esi+32]
    push dword ptr [esi+28]
    push edi
    push offset stack_fmt
    call crt_printf
    add esp, 16
    
    push call_depth
    push offset ret_fmt
    call crt_printf
    add esp, 8
    
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret 4
display_func_exit ENDP

; 显示 CALL 返回后
display_call_after PROC
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    mov esi, [ebp+8]
    
    ; 获取缩进
    mov eax, call_depth
    call get_indent
    mov edi, eax
    
    push offset call_after_name
    push edi
    push dword ptr [esi]
    push offset entry_fmt
    call crt_printf
    add esp, 16
    
    push dword ptr [esi+4]
    push offset entry_detail
    call crt_printf
    add esp, 8
    
    push dword ptr [esi+24]
    push dword ptr [esi+20]
    push dword ptr [esi+16]
    push dword ptr [esi+12]
    push edi
    push offset reg_fmt
    call crt_printf
    add esp, 24
    
    ; 显示栈（检查是否有变化）
    mov eax, [esi+28]
    mov ebx, prev_esp
    cmp ebx, 0
    je no_prev_ca
    
    cmp eax, ebx
    je no_esp_change_ca
    
    ; ESP 有变化
    push eax
    sub eax, ebx
    
    push dword ptr [esi+32]
    push dword ptr [esi+28]
    push edi
    push offset stack_fmt
    call crt_printf
    add esp, 16
    
    pop eax
    sub eax, ebx
    push eax
    push dword ptr [esi+28]
    push ebx
    push offset stack_change_fmt
    call crt_printf
    add esp, 12
    jmp done_stack_ca
    
no_esp_change_ca:
no_prev_ca:
    push dword ptr [esi+32]
    push dword ptr [esi+28]
    push edi
    push offset stack_fmt
    call crt_printf
    add esp, 16
    
    push offset stack_no_change_fmt
    call crt_printf
    add esp, 4
    
done_stack_ca:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret 4
display_call_after ENDP

; 显示 CALL 指令条目（保留兼容性）
display_call_entry PROC
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    ; ESI 指向当前条目
    mov esi, [ebp+8]
    
    ; 获取缩进（使用当前深度-1，因为还没显示）
    mov eax, call_depth
    dec eax
    call get_indent
    mov edi, eax
    
    ; 显示条目
    push offset call_name
    push edi
    push dword ptr [esi]
    push offset entry_fmt
    call crt_printf
    add esp, 16
    
    ; 显示 EIP
    push dword ptr [esi+4]
    push offset entry_detail
    call crt_printf
    add esp, 8
    
    ; 显示寄存器
    push dword ptr [esi+24]
    push dword ptr [esi+20]
    push dword ptr [esi+16]
    push dword ptr [esi+12]
    push edi
    push offset reg_fmt
    call crt_printf
    add esp, 24
    
    ; 显示栈和深度
    push dword ptr [esi+32]
    push dword ptr [esi+28]
    push edi
    push offset stack_fmt
    call crt_printf
    add esp, 16
    
    push call_depth
    push offset call_fmt
    call crt_printf
    add esp, 8
    
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret 4
display_call_entry ENDP

; 显示 RET 指令条目
display_ret_entry PROC
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    mov esi, [ebp+8]
    
    ; 获取缩进（使用返回后的深度）
    mov eax, call_depth
    call get_indent
    mov edi, eax
    
    ; 显示条目
    push offset ret_name
    push edi
    push dword ptr [esi]
    push offset entry_fmt
    call crt_printf
    add esp, 16
    
    push dword ptr [esi+4]
    push offset entry_detail
    call crt_printf
    add esp, 8
    
    push dword ptr [esi+24]
    push dword ptr [esi+20]
    push dword ptr [esi+16]
    push dword ptr [esi+12]
    push edi
    push offset reg_fmt
    call crt_printf
    add esp, 24
    
    push dword ptr [esi+32]
    push dword ptr [esi+28]
    push edi
    push offset stack_fmt
    call crt_printf
    add esp, 16
    
    push call_depth
    push offset ret_fmt
    call crt_printf
    add esp, 8
    
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret 4
display_ret_entry ENDP

; 显示普通指令条目
display_normal_entry PROC
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    mov esi, [ebp+8]
    
    ; 获取缩进
    mov eax, call_depth
    call get_indent
    mov edi, eax
    
    ; 获取指令名称
    mov edx, [esi+8]
    dec edx
    cmp edx, 11                     ; 现在有12种指令类型（0-11）
    ja use_unknown
    mov ebx, [inst_names + edx*4]
    jmp got_name
use_unknown:
    mov ebx, offset unknown_name
got_name:
    
    ; 显示条目
    push ebx
    push edi
    push dword ptr [esi]
    push offset entry_fmt
    call crt_printf
    add esp, 16
    
    push dword ptr [esi+4]
    push offset entry_detail
    call crt_printf
    add esp, 8
    
    push dword ptr [esi+24]
    push dword ptr [esi+20]
    push dword ptr [esi+16]
    push dword ptr [esi+12]
    push edi
    push offset reg_fmt
    call crt_printf
    add esp, 24
    
    ; 显示栈（检查是否有变化）
    mov eax, [esi+28]
    mov ebx, prev_esp
    cmp ebx, 0
    je no_prev
    
    cmp eax, ebx
    je no_esp_change
    
    ; ESP 有变化 - 计算差值
    push eax                    ; 保存当前 ESP
    sub eax, ebx                ; 计算变化量
    
    push dword ptr [esi+32]
    push dword ptr [esi+28]
    push edi
    push offset stack_fmt
    call crt_printf
    add esp, 16
    
    pop eax                     ; 恢复当前 ESP
    sub eax, ebx                ; 重新计算变化量
    push eax
    push dword ptr [esi+28]
    push ebx
    push offset stack_change_fmt
    call crt_printf
    add esp, 12
    jmp done_stack
    
no_esp_change:
no_prev:
    push dword ptr [esi+32]
    push dword ptr [esi+28]
    push edi
    push offset stack_fmt
    call crt_printf
    add esp, 16
    
    push offset stack_no_change_fmt
    call crt_printf
    add esp, 4
    
done_stack:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret 4
display_normal_entry ENDP

; 显示 ESP 不匹配警告
display_esp_mismatch_warning PROC
    push ebp
    mov ebp, esp
    
    mov eax, call_depth
    call get_indent
    
    push dword ptr [ebp+8]
    push dword ptr [ebp+12]
    push eax
    push offset warn_esp_mismatch
    call crt_printf
    add esp, 16
    
    pop ebp
    ret
display_esp_mismatch_warning ENDP

; 显示 RET 不匹配警告
display_ret_mismatch_warning PROC
    push ebp
    mov ebp, esp
    
    mov eax, call_depth
    call get_indent
    
    push eax
    push offset warn_ret_mismatch
    call crt_printf
    add esp, 8
    
    pop ebp
    ret
display_ret_mismatch_warning ENDP

; 显示摘要
display_summary PROC
    push ebp
    mov ebp, esp
    
    invoke crt_printf, offset summary_header
    invoke crt_printf, offset summary_total, entry_count
    invoke crt_printf, offset summary_calls, call_count
    invoke crt_printf, offset summary_rets, ret_count
    invoke crt_printf, offset summary_max_depth, max_call_depth
    invoke crt_printf, offset summary_warnings, warning_count
    
    ; 显示最终调用深度
    mov eax, call_depth
    push eax
    push offset summary_final_depth
    call crt_printf
    add esp, 8
    
    ; 检查是否正常
    cmp call_depth, 0
    je depth_ok
    
    invoke crt_printf, offset summary_err
    jmp done
    
depth_ok:
    invoke crt_printf, offset summary_ok
    
done:
    pop ebp
    ret
display_summary ENDP

END start
