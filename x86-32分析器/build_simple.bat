@echo off
echo ========================================
echo 构建简单示例
echo ========================================

if exist execution_trace.bin del execution_trace.bin

D:\masm32\bin\ml /c /coff /nologo trace_buffer_fixed.asm
D:\masm32\bin\ml /c /coff /nologo trace_writer_fixed.asm
D:\masm32\bin\ml /c /coff /nologo test_simple.asm

D:\masm32\bin\Link /SUBSYSTEM:CONSOLE /OUT:test_simple.exe /nologo ^
    test_simple.obj trace_buffer_fixed.obj trace_writer_fixed.obj

echo.
echo 运行程序...
test_simple.exe

echo.
echo 分析轨迹...
trace_analyzer.exe
