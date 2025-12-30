@echo off
echo ========================================
echo 构建增强版轨迹分析器
echo ========================================

REM 编译
echo 编译 trace_analyzer.asm...
D:\masm32\bin\ml /c /coff trace_analyzer.asm
if errorlevel 1 (
    echo 编译失败！
    pause
    exit /b 1
)

REM 链接
echo 链接 trace_analyzer.exe...
D:\masm32\bin\Link /SUBSYSTEM:CONSOLE /OUT:trace_analyzer.exe trace_analyzer.obj
if errorlevel 1 (
    echo 链接失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 构建成功！
echo ========================================
echo.

REM 检查轨迹文件
if not exist execution_trace.bin (
    echo 未找到轨迹文件，先运行测试程序...
    if exist test_complete.exe (
        echo 运行 test_complete.exe...
        test_complete.exe
        echo.
    ) else (
        echo 请先运行 build_complete.bat 生成轨迹文件
        pause
        exit /b 0
    )
)

echo ========================================
echo 运行增强版分析器
echo ========================================
echo.
trace_analyzer.exe

pause
