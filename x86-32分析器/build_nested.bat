@echo off
if exist execution_trace.bin del execution_trace.bin
D:\masm32\bin\ml /c /coff /nologo trace_buffer_fixed.asm
D:\masm32\bin\ml /c /coff /nologo trace_writer_fixed.asm
D:\masm32\bin\ml /c /coff /nologo test_nested.asm
D:\masm32\bin\Link /SUBSYSTEM:CONSOLE /OUT:test_nested.exe /nologo test_nested.obj trace_buffer_fixed.obj trace_writer_fixed.obj
test_nested.exe
trace_analyzer.exe
