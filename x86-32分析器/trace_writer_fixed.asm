; trace_writer.asm - 轨迹数据写入文件模块（修复版）

.386
.model flat, stdcall
option casemap:none

include D:\masm32\include\windows.inc
include D:\masm32\include\kernel32.inc
includelib D:\masm32\lib\kernel32.lib

extern C get_trace_data:proc

.data
    trace_file_name db "execution_trace.bin", 0
    
    ; 文件头结构
    trace_header db "TRACE001"          ; 文件标识（8字节）
    
    ; 消息
    msg_success db "轨迹数据已写入: execution_trace.bin", 0Dh, 0Ah, 0
    msg_no_data db "没有轨迹数据需要写入", 0Dh, 0Ah, 0
    msg_error db "写入轨迹文件失败", 0Dh, 0Ah, 0

.data?
    file_handle dd ?
    bytes_written dd ?
    entry_count dd ?
    buffer_addr dd ?

.code

; 写入轨迹数据到文件
PUBLIC write_trace_file
write_trace_file PROC C
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    
    ; 获取轨迹数据
    call get_trace_data
    ; 返回: EAX = 条目数, EDX = 缓冲区地址
    
    mov entry_count, eax
    mov buffer_addr, edx
    
    cmp eax, 0
    je no_data_to_write
    
    ; 创建文件
    invoke CreateFileA, offset trace_file_name, GENERIC_WRITE, 0, 0, \
                        CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0
    
    cmp eax, INVALID_HANDLE_VALUE
    je error_file_open
    mov file_handle, eax
    
    ; 写入文件头（8字节）
    invoke WriteFile, file_handle, offset trace_header, 8, \
                      offset bytes_written, 0
    
    cmp eax, 0
    je error_file_write
    
    ; 计算数据大小: 条目数 * 36
    mov eax, entry_count
    mov ecx, 36
    mul ecx                         ; EAX = 总字节数
    
    ; 写入轨迹数据
    invoke WriteFile, file_handle, buffer_addr, eax, \
                      offset bytes_written, 0
    
    cmp eax, 0
    je error_file_write
    
    ; 关闭文件
    invoke CloseHandle, file_handle
    
    ; 显示成功消息
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    mov ebx, eax
    invoke WriteFile, ebx, offset msg_success, sizeof msg_success, \
                      offset bytes_written, 0
    
    jmp done
    
error_file_open:
error_file_write:
    ; 关闭文件（如果已打开）
    cmp file_handle, INVALID_HANDLE_VALUE
    je skip_close
    invoke CloseHandle, file_handle
skip_close:
    
    ; 显示错误消息
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    mov ebx, eax
    invoke WriteFile, ebx, offset msg_error, sizeof msg_error, \
                      offset bytes_written, 0
    jmp done
    
no_data_to_write:
    ; 显示无数据消息
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    mov ebx, eax
    invoke WriteFile, ebx, offset msg_no_data, sizeof msg_no_data, \
                      offset bytes_written, 0
    
done:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret
write_trace_file ENDP

END
