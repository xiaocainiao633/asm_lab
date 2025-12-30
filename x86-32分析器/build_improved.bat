@echo off
echo ========================================
echo 构建改进版测试程序
echo ========================================

REM 清理
if exist *.obj del /Q *.obj 2>nul
if exist test_improved.exe del /Q test_improved.exe 2>nul
if exist execution_trace.bin del /Q execution_trace.bin 2>nul

REM 编译核心模块
echo [1/4] 编译 trace_buffer_fixed.asm...
D:\masm32\bin\ml /c /coff /nologo trace_buffer_fixed.asm
if errorlevel 1 goto error

echo [2/4] 编译 trace_writer_fixed.asm...
D:\masm32\bin\ml /c /coff /nologo trace_writer_fixed.asm
if errorlevel 1 goto error

echo [3/4] 编译 test_improved.asm...
D:\masm32\bin\ml /c /coff /nologo test_improved.asm
if errorlevel 1 goto error

REM 链接
echo [4/4] 链接 test_improved.exe...
D:\masm32\bin\Link /SUBSYSTEM:CONSOLE /OUT:test_improved.exe /nologo ^
    test_improved.obj trace_buffer_fixed.obj trace_writer_fixed.obj
if errorlevel 1 goto error

echo.
echo ========================================
echo 构建成功！运行测试...
echo ========================================
echo.
test_improved.exe

echo.
echo ========================================
echo 重新编译分析器...
echo ========================================
D:\masm32\bin\ml /c /coff /nologo trace_analyzer.asm
if errorlevel 1 goto error

D:\masm32\bin\Link /SUBSYSTEM:CONSOLE /OUT:trace_analyzer.exe /nologo trace_analyzer.obj
if errorlevel 1 goto error

echo.
echo ========================================
echo 运行分析器
echo ========================================
echo.
trace_analyzer.exe

goto end

:error
echo.
echo 构建失败！
pause
exit /b 1

:end
pause
