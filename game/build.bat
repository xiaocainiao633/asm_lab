@echo off
echo 正在编译贪吃蛇游戏...

REM 设置 MASM32 路径（根据实际安装路径调整）
set MASM32=D:\masm32

REM 汇编
%MASM32%\bin\ml /c /coff /Cp SnakeGame.asm
if errorlevel 1 goto error

REM 链接
%MASM32%\bin\link /SUBSYSTEM:WINDOWS /LIBPATH:%MASM32%\lib SnakeGame.obj
if errorlevel 1 goto error

echo.
echo 编译成功！
echo 可执行文件: SnakeGame.exe
echo.
pause
goto end

:error
echo.
echo 编译失败！请检查错误信息。
echo.
pause

:end
