@echo off
echo 启动贪吃蛇游戏...
echo.

if not exist SnakeGame.exe (
    echo 错误: SnakeGame.exe 不存在！
    echo 请先运行 build.bat 编译程序。
    echo.
    pause
    exit
)

start SnakeGame.exe
