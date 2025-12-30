@echo off
echo ========================================
echo Build Extreme Test Cases
echo ========================================

REM Clean
if exist *.obj del /Q *.obj 2>nul
if exist test_extreme.exe del /Q test_extreme.exe 2>nul
if exist execution_trace.bin del /Q execution_trace.bin 2>nul

REM Compile
echo [1/4] Compiling trace_buffer_fixed.asm...
D:\masm32\bin\ml /c /coff /nologo trace_buffer_fixed.asm
if errorlevel 1 goto error

echo [2/4] Compiling trace_writer_fixed.asm...
D:\masm32\bin\ml /c /coff /nologo trace_writer_fixed.asm
if errorlevel 1 goto error

echo [3/4] Compiling test_extreme.asm...
D:\masm32\bin\ml /c /coff /nologo test_extreme.asm
if errorlevel 1 goto error

echo [4/4] Linking test_extreme.exe...
D:\masm32\bin\Link /SUBSYSTEM:CONSOLE /OUT:test_extreme.exe /nologo ^
    test_extreme.obj trace_buffer_fixed.obj trace_writer_fixed.obj
if errorlevel 1 goto error

echo.
echo ========================================
echo Build Success! Running test...
echo ========================================
echo.
test_extreme.exe

echo.
echo ========================================
echo Analyzing trace...
echo ========================================
echo.
trace_analyzer.exe

goto end

:error
echo.
echo Build failed!
pause
exit /b 1

:end
pause
