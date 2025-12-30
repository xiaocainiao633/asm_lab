.386
.model flat, stdcall
option casemap:none

include \masm32\include\windows.inc
include \masm32\include\kernel32.inc
include \masm32\include\user32.inc
include \masm32\include\gdi32.inc

includelib \masm32\lib\kernel32.lib
includelib \masm32\lib\user32.lib
includelib \masm32\lib\gdi32.lib

; ============================================
; 函数声明
; ============================================
WinMain PROTO :DWORD, :DWORD, :DWORD, :DWORD
WndProc PROTO :DWORD, :DWORD, :DWORD, :DWORD
InitGame PROTO
InitAISnake PROTO
GenerateFood PROTO
CheckFoodCollision PROTO
ProcessKeyboard PROTO :DWORD
GameLoop PROTO
AIGameLoop PROTO
DrawGame PROTO :DWORD
LoadHighScore PROTO
SaveHighScore PROTO

; ============================================
; 常量定义
; ============================================
GRID_SIZE       equ 20
CELL_SIZE       equ 30
MAX_LEN         equ 400
MAX_AI_SNAKES   equ 3
TIMER_ID        equ 1
INITIAL_SPEED   equ 150
WINDOW_WIDTH    equ 800
WINDOW_HEIGHT   equ 680

DIR_UP          equ 0
DIR_DOWN        equ 1
DIR_LEFT        equ 2
DIR_RIGHT       equ 3

; Button IDs
BTN_PAUSE       equ 1001
BTN_RESTART     equ 1002
BTN_COLOR1      equ 1003
BTN_COLOR2      equ 1004
BTN_COLOR3      equ 1005
BTN_COLOR4      equ 1006
BTN_AI_TOGGLE   equ 1007
BTN_AI_COUNT    equ 1008

; ============================================
; 数据段
; ============================================
.data
    szClassName     db "SnakeGameClass", 0
    szAppName       db "Snake Game - Enhanced", 0
    szScore         db "SCORE: %d  |  LEVEL: %d  |  LENGTH: %d", 0
    szHighScoreInfo db "BEST SCORE: %d", 0
    szGameOver      db "GAME OVER! Score: %d", 13, 10, 10, "Click Restart or press ENTER", 0
    szPaused        db "= = PAUSED = =", 0
    szControls      db "Arrow Keys: Move | Or use buttons on the right", 0
    szColorInfo     db "Choose Snake Color:", 0
    szFileName      db "highscore.dat", 0
    
    szBtnPause      db "PAUSE", 0
    szBtnResume     db "RESUME", 0
    szBtnRestart    db "RESTART", 0
    szBtnGreen      db "Green", 0
    szBtnBlue       db "Blue", 0
    szBtnPurple     db "Purple", 0
    szBtnOrange     db "Orange", 0
    szBtnAIOn       db "AI: ON", 0
    szBtnAIOff      db "AI: OFF", 0
    szBtnAICount0   db "AI: 0", 0
    szBtnAICount1   db "AI: 1", 0
    szBtnAICount2   db "AI: 2", 0
    szBtnAICount3   db "AI: 3", 0
    szButton        db "BUTTON", 0
    
    SnakeX          DWORD MAX_LEN DUP(?)
    SnakeY          DWORD MAX_LEN DUP(?)
    SnakeLen        DWORD 3
    Direction       DWORD DIR_RIGHT
    NextDirection   DWORD DIR_RIGHT
    
    ; AI Snakes (multiple)
    AISnakeX        DWORD MAX_AI_SNAKES * MAX_LEN DUP(?)
    AISnakeY        DWORD MAX_AI_SNAKES * MAX_LEN DUP(?)
    AISnakeLen      DWORD MAX_AI_SNAKES DUP(?)
    AIDirection     DWORD MAX_AI_SNAKES DUP(?)
    AIActive        DWORD MAX_AI_SNAKES DUP(?)
    AICount         DWORD 0
    AIEnabled       DWORD 0
    
    FoodX           DWORD 10
    FoodY           DWORD 10
    
    Score           DWORD 0
    HighScore       DWORD 0
    GameSpeed       DWORD INITIAL_SPEED
    
    bGameOver       DWORD 0
    bPaused         DWORD 0
    
    SnakeHeadColor  DWORD 000FF00h
    SnakeBodyColor  DWORD 0088008h
    
    hInstance       DWORD ?
    hWnd            DWORD ?
    hBtnPause       DWORD ?
    hBtnRestart     DWORD ?
    hBtnColor1      DWORD ?
    hBtnColor2      DWORD ?
    hBtnColor3      DWORD ?
    hBtnColor4      DWORD ?
    hBtnAI          DWORD ?
    hBtnAICount     DWORD ?

.data?
    buffer          db 100 dup(?)

.code

start:
    invoke GetModuleHandle, NULL
    mov hInstance, eax
    
    invoke LoadHighScore
    invoke WinMain, hInstance, NULL, NULL, SW_SHOWDEFAULT
    invoke ExitProcess, eax

WinMain proc hInst:DWORD, hPrevInst:DWORD, CmdLine:DWORD, CmdShow:DWORD
    LOCAL wc:WNDCLASSEX
    LOCAL msg:MSG
    LOCAL hwnd:DWORD
    
    mov wc.cbSize, sizeof WNDCLASSEX
    mov wc.style, CS_HREDRAW or CS_VREDRAW
    mov wc.lpfnWndProc, offset WndProc
    mov wc.cbClsExtra, 0
    mov wc.cbWndExtra, 0
    push hInst
    pop wc.hInstance
    invoke LoadIcon, NULL, IDI_APPLICATION
    mov wc.hIcon, eax
    invoke LoadCursor, NULL, IDC_ARROW
    mov wc.hCursor, eax
    mov wc.hbrBackground, COLOR_WINDOW+1
    mov wc.lpszMenuName, NULL
    mov wc.lpszClassName, offset szClassName
    mov wc.hIconSm, 0
    
    invoke RegisterClassEx, addr wc
    
    invoke CreateWindowEx, 0, addr szClassName, addr szAppName,
           WS_OVERLAPPED or WS_CAPTION or WS_SYSMENU or WS_MINIMIZEBOX,
           CW_USEDEFAULT, CW_USEDEFAULT, 
           WINDOW_WIDTH, WINDOW_HEIGHT,
           NULL, NULL, hInst, NULL
    mov hwnd, eax
    mov hWnd, eax
    
    invoke ShowWindow, hwnd, SW_SHOWNORMAL
    invoke UpdateWindow, hwnd
    
    .while TRUE
        invoke GetMessage, addr msg, NULL, 0, 0
        .break .if (!eax)
        invoke TranslateMessage, addr msg
        invoke DispatchMessage, addr msg
    .endw
    
    mov eax, msg.wParam
    ret
WinMain endp

WndProc proc hWin:DWORD, uMsg:DWORD, wParam:DWORD, lParam:DWORD
    LOCAL ps:PAINTSTRUCT
    LOCAL hdc:DWORD
    
    .if uMsg == WM_CREATE
        invoke InitGame
        invoke SetTimer, hWin, TIMER_ID, GameSpeed, NULL
        
        ; Create buttons
        invoke CreateWindowEx, 0, addr szButton, addr szBtnPause,
               WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON,
               630, 20, 140, 40,
               hWin, BTN_PAUSE, hInstance, NULL
        mov hBtnPause, eax
        
        invoke CreateWindowEx, 0, addr szButton, addr szBtnRestart,
               WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON,
               630, 70, 140, 40,
               hWin, BTN_RESTART, hInstance, NULL
        mov hBtnRestart, eax
        
        invoke CreateWindowEx, 0, addr szButton, addr szBtnGreen,
               WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON,
               630, 150, 140, 35,
               hWin, BTN_COLOR1, hInstance, NULL
        mov hBtnColor1, eax
        
        invoke CreateWindowEx, 0, addr szButton, addr szBtnBlue,
               WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON,
               630, 190, 140, 35,
               hWin, BTN_COLOR2, hInstance, NULL
        mov hBtnColor2, eax
        
        invoke CreateWindowEx, 0, addr szButton, addr szBtnPurple,
               WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON,
               630, 230, 140, 35,
               hWin, BTN_COLOR3, hInstance, NULL
        mov hBtnColor3, eax
        
        invoke CreateWindowEx, 0, addr szButton, addr szBtnOrange,
               WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON,
               630, 270, 140, 35,
               hWin, BTN_COLOR4, hInstance, NULL
        mov hBtnColor4, eax
        
        invoke CreateWindowEx, 0, addr szButton, addr szBtnAIOff,
               WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON,
               630, 360, 140, 40,
               hWin, BTN_AI_TOGGLE, hInstance, NULL
        mov hBtnAI, eax
        
        invoke CreateWindowEx, 0, addr szButton, addr szBtnAICount0,
               WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON,
               630, 410, 140, 40,
               hWin, BTN_AI_COUNT, hInstance, NULL
        mov hBtnAICount, eax
        
    .elseif uMsg == WM_COMMAND
        mov eax, wParam
        and eax, 0FFFFh
        
        .if eax == BTN_PAUSE
            .if bGameOver == 0
                mov eax, bPaused
                xor eax, 1
                mov bPaused, eax
                .if bPaused == 1
                    invoke SetWindowText, hBtnPause, addr szBtnResume
                .else
                    invoke SetWindowText, hBtnPause, addr szBtnPause
                .endif
                invoke InvalidateRect, hWin, NULL, TRUE
            .endif
            
        .elseif eax == BTN_RESTART
            invoke InitGame
            mov bPaused, 0
            invoke SetWindowText, hBtnPause, addr szBtnPause
            invoke InvalidateRect, hWin, NULL, TRUE
            
        .elseif eax == BTN_COLOR1
            mov SnakeHeadColor, 000FF00h
            mov SnakeBodyColor, 0088008h
            invoke InvalidateRect, hWin, NULL, TRUE
            
        .elseif eax == BTN_COLOR2
            mov SnakeHeadColor, 0FF0000h
            mov SnakeBodyColor, 0880000h
            invoke InvalidateRect, hWin, NULL, TRUE
            
        .elseif eax == BTN_COLOR3
            mov SnakeHeadColor, 0FF00FFh
            mov SnakeBodyColor, 0880088h
            invoke InvalidateRect, hWin, NULL, TRUE
            
        .elseif eax == BTN_COLOR4
            mov SnakeHeadColor, 0008AFFh
            mov SnakeBodyColor, 0005588h
            invoke InvalidateRect, hWin, NULL, TRUE
            
        .elseif eax == BTN_AI_TOGGLE
            mov eax, AIEnabled
            xor eax, 1
            mov AIEnabled, eax
            .if AIEnabled == 1
                invoke SetWindowText, hBtnAI, addr szBtnAIOn
                invoke InitAISnake
            .else
                invoke SetWindowText, hBtnAI, addr szBtnAIOff
                ; Clear all AI snakes
                mov ecx, 0
                .while ecx < MAX_AI_SNAKES
                    mov eax, ecx
                    shl eax, 2
                    mov ebx, offset AISnakeLen
                    add ebx, eax
                    mov DWORD PTR [ebx], 0
                    mov ebx, offset AIActive
                    add ebx, eax
                    mov DWORD PTR [ebx], 0
                    inc ecx
                .endw
            .endif
            invoke InvalidateRect, hWin, NULL, TRUE
            
        .elseif eax == BTN_AI_COUNT
            ; Cycle through 0, 1, 2, 3
            mov eax, AICount
            inc eax
            .if eax > MAX_AI_SNAKES
                xor eax, eax
            .endif
            mov AICount, eax
            
            ; Update button text
            .if AICount == 0
                invoke SetWindowText, hBtnAICount, addr szBtnAICount0
            .elseif AICount == 1
                invoke SetWindowText, hBtnAICount, addr szBtnAICount1
            .elseif AICount == 2
                invoke SetWindowText, hBtnAICount, addr szBtnAICount2
            .else
                invoke SetWindowText, hBtnAICount, addr szBtnAICount3
            .endif
            
            ; Reinitialize AI snakes if enabled
            .if AIEnabled == 1
                invoke InitAISnake
            .endif
            invoke InvalidateRect, hWin, NULL, TRUE
        .endif
        
    .elseif uMsg == WM_TIMER
        mov eax, bGameOver
        .if eax == 0
            mov eax, bPaused
            .if eax == 0
                invoke GameLoop
                .if AIEnabled == 1
                    invoke AIGameLoop
                .endif
                invoke InvalidateRect, hWin, NULL, TRUE
            .endif
        .endif
        
    .elseif uMsg == WM_KEYDOWN
        invoke ProcessKeyboard, wParam
        invoke InvalidateRect, hWin, NULL, TRUE
        
    .elseif uMsg == WM_PAINT
        invoke BeginPaint, hWin, addr ps
        mov hdc, eax
        invoke DrawGame, hdc
        invoke EndPaint, hWin, addr ps
        
    .elseif uMsg == WM_DESTROY
        invoke SaveHighScore
        invoke KillTimer, hWin, TIMER_ID
        invoke PostQuitMessage, 0
        
    .else
        invoke DefWindowProc, hWin, uMsg, wParam, lParam
        ret
    .endif
    
    xor eax, eax
    ret
WndProc endp

InitGame proc
    mov SnakeLen, 3
    mov Direction, DIR_RIGHT
    mov NextDirection, DIR_RIGHT
    
    mov eax, GRID_SIZE
    shr eax, 1
    mov SnakeX[0], eax
    mov SnakeY[0], eax
    
    dec eax
    mov SnakeX[4], eax
    mov eax, GRID_SIZE
    shr eax, 1
    mov SnakeY[4], eax
    
    mov eax, GRID_SIZE
    shr eax, 1
    sub eax, 2
    mov SnakeX[8], eax
    mov eax, GRID_SIZE
    shr eax, 1
    mov SnakeY[8], eax
    
    mov Score, 0
    mov bGameOver, 0
    mov bPaused, 0
    mov GameSpeed, INITIAL_SPEED
    
    .if AIEnabled == 1
        invoke InitAISnake
    .endif
    
    invoke GenerateFood
    ret
InitGame endp

InitAISnake proc
    LOCAL aiIndex:DWORD
    LOCAL startX:DWORD
    LOCAL startY:DWORD
    
    ; Clear all AI snakes first
    mov ecx, 0
@@ClearLoop:
    cmp ecx, MAX_AI_SNAKES
    jge @@ClearDone
        mov eax, ecx
        shl eax, 2
        mov ebx, offset AISnakeLen
        add ebx, eax
        mov DWORD PTR [ebx], 0
        mov ebx, offset AIActive
        add ebx, eax
        mov DWORD PTR [ebx], 0
        inc ecx
        jmp @@ClearLoop
@@ClearDone:
    
    ; Initialize AICount number of snakes
    mov aiIndex, 0
@@InitLoop:
    mov eax, aiIndex
    cmp eax, AICount
    jge @@InitDone
        ; Set active
        mov eax, aiIndex
        shl eax, 2
        mov ebx, offset AIActive
        add ebx, eax
        mov DWORD PTR [ebx], 1
        
        ; Set length
        mov ebx, offset AISnakeLen
        add ebx, eax
        mov DWORD PTR [ebx], 3
        
        ; Set direction
        mov ebx, offset AIDirection
        add ebx, eax
        mov DWORD PTR [ebx], DIR_LEFT
        
        ; Calculate starting position based on index
        mov eax, GRID_SIZE
        shr eax, 1
        mov ecx, aiIndex
        .if ecx == 0
            add eax, 5
        .elseif ecx == 1
            add eax, 8
        .else
            add eax, 2
        .endif
        mov startX, eax
        
        mov eax, GRID_SIZE
        shr eax, 1
        mov ecx, aiIndex
        .if ecx == 1
            add eax, 5
        .elseif ecx == 2
            sub eax, 5
        .endif
        mov startY, eax
        
        ; Set head position
        mov eax, aiIndex
        mov ecx, MAX_LEN
        mul ecx
        shl eax, 2
        mov ebx, offset AISnakeX
        add ebx, eax
        mov edx, startX
        mov [ebx], edx
        
        mov eax, aiIndex
        mov ecx, MAX_LEN
        mul ecx
        shl eax, 2
        mov ebx, offset AISnakeY
        add ebx, eax
        mov edx, startY
        mov [ebx], edx
        
        ; Set body segment 1
        mov eax, aiIndex
        mov ecx, MAX_LEN
        mul ecx
        inc eax
        shl eax, 2
        mov ebx, offset AISnakeX
        add ebx, eax
        mov edx, startX
        inc edx
        mov [ebx], edx
        
        mov eax, aiIndex
        mov ecx, MAX_LEN
        mul ecx
        inc eax
        shl eax, 2
        mov ebx, offset AISnakeY
        add ebx, eax
        mov edx, startY
        mov [ebx], edx
        
        ; Set body segment 2
        mov eax, aiIndex
        mov ecx, MAX_LEN
        mul ecx
        add eax, 2
        shl eax, 2
        mov ebx, offset AISnakeX
        add ebx, eax
        mov edx, startX
        add edx, 2
        mov [ebx], edx
        
        mov eax, aiIndex
        mov ecx, MAX_LEN
        mul ecx
        add eax, 2
        shl eax, 2
        mov ebx, offset AISnakeY
        add ebx, eax
        mov edx, startY
        mov [ebx], edx
        
        inc aiIndex
        jmp @@InitLoop
@@InitDone:
    
    ret
InitAISnake endp

GenerateFood proc
    @@:
    invoke GetTickCount
    xor edx, edx
    mov ecx, GRID_SIZE
    div ecx
    mov FoodX, edx
    
    invoke GetTickCount
    add eax, 12345
    xor edx, edx
    mov ecx, GRID_SIZE
    div ecx
    mov FoodY, edx
    
    invoke CheckFoodCollision
    .if eax == 1
        jmp @B
    .endif
    
    ret
GenerateFood endp

CheckFoodCollision proc
    LOCAL i:DWORD
    
    mov i, 0
    mov ecx, SnakeLen
    .while i < ecx
        mov eax, i
        shl eax, 2
        mov ebx, offset SnakeX
        add ebx, eax
        mov edx, [ebx]
        
        .if edx == FoodX
            mov ebx, offset SnakeY
            add ebx, eax
            mov edx, [ebx]
            .if edx == FoodY
                mov eax, 1
                ret
            .endif
        .endif
        
        inc i
    .endw
    
    xor eax, eax
    ret
CheckFoodCollision endp

ProcessKeyboard proc wParam:DWORD
    .if wParam == VK_UP
        .if Direction != DIR_DOWN
            mov NextDirection, DIR_UP
        .endif
    .elseif wParam == VK_DOWN
        .if Direction != DIR_UP
            mov NextDirection, DIR_DOWN
        .endif
    .elseif wParam == VK_LEFT
        .if Direction != DIR_RIGHT
            mov NextDirection, DIR_LEFT
        .endif
    .elseif wParam == VK_RIGHT
        .if Direction != DIR_LEFT
            mov NextDirection, DIR_RIGHT
        .endif
    .elseif wParam == VK_SPACE
        .if bGameOver == 0
            mov eax, bPaused
            xor eax, 1
            mov bPaused, eax
            .if bPaused == 1
                invoke SetWindowText, hBtnPause, addr szBtnResume
            .else
                invoke SetWindowText, hBtnPause, addr szBtnPause
            .endif
        .endif
    .elseif wParam == VK_RETURN
        .if bGameOver == 1
            invoke InitGame
            mov bPaused, 0
            invoke SetWindowText, hBtnPause, addr szBtnPause
        .endif
    .elseif wParam == 31h
        mov SnakeHeadColor, 000FF00h
        mov SnakeBodyColor, 0088008h
    .elseif wParam == 32h
        mov SnakeHeadColor, 0FF0000h
        mov SnakeBodyColor, 0880000h
    .elseif wParam == 33h
        mov SnakeHeadColor, 0FF00FFh
        mov SnakeBodyColor, 0880088h
    .elseif wParam == 34h
        mov SnakeHeadColor, 0008AFFh
        mov SnakeBodyColor, 0005588h
    .endif
    ret
ProcessKeyboard endp


GameLoop proc
    LOCAL i:DWORD
    LOCAL newX:DWORD
    LOCAL newY:DWORD
    LOCAL ateFood:DWORD
    
    mov ateFood, 0
    mov eax, NextDirection
    mov Direction, eax
    
    mov eax, SnakeX[0]
    mov newX, eax
    mov eax, SnakeY[0]
    mov newY, eax
    
    .if Direction == DIR_UP
        dec newY
    .elseif Direction == DIR_DOWN
        inc newY
    .elseif Direction == DIR_LEFT
        dec newX
    .elseif Direction == DIR_RIGHT
        inc newX
    .endif
    
    ; Check wall
    mov eax, newX
    .if eax < 0
        mov bGameOver, 1
        invoke wsprintf, addr buffer, addr szGameOver, Score
        invoke MessageBox, hWnd, addr buffer, addr szAppName, MB_OK
        ret
    .endif
    .if eax >= GRID_SIZE
        mov bGameOver, 1
        invoke wsprintf, addr buffer, addr szGameOver, Score
        invoke MessageBox, hWnd, addr buffer, addr szAppName, MB_OK
        ret
    .endif
    
    mov eax, newY
    .if eax < 0
        mov bGameOver, 1
        invoke wsprintf, addr buffer, addr szGameOver, Score
        invoke MessageBox, hWnd, addr buffer, addr szAppName, MB_OK
        ret
    .endif
    .if eax >= GRID_SIZE
        mov bGameOver, 1
        invoke wsprintf, addr buffer, addr szGameOver, Score
        invoke MessageBox, hWnd, addr buffer, addr szAppName, MB_OK
        ret
    .endif
    
    ; Check self collision
    mov i, 1
    mov ecx, SnakeLen
    .while i < ecx
        mov eax, i
        shl eax, 2
        mov ebx, offset SnakeX
        add ebx, eax
        mov edx, [ebx]
        
        .if edx == newX
            mov ebx, offset SnakeY
            add ebx, eax
            mov edx, [ebx]
            .if edx == newY
                mov bGameOver, 1
                invoke wsprintf, addr buffer, addr szGameOver, Score
                invoke MessageBox, hWnd, addr buffer, addr szAppName, MB_OK
                ret
            .endif
        .endif
        
        inc i
    .endw
    
    ; Check food
    mov eax, newX
    .if eax == FoodX
        mov eax, newY
        .if eax == FoodY
            mov ateFood, 1
            inc Score
            
            mov eax, Score
            xor edx, edx
            mov ecx, 5
            div ecx
            .if edx == 0
                mov eax, GameSpeed
                .if eax > 50
                    sub eax, 10
                    mov GameSpeed, eax
                    invoke KillTimer, hWnd, TIMER_ID
                    invoke SetTimer, hWnd, TIMER_ID, GameSpeed, NULL
                .endif
            .endif
            
            mov eax, Score
            .if eax > HighScore
                mov HighScore, eax
            .endif
            
            invoke GenerateFood
        .endif
    .endif
    
    ; Move snake
    .if ateFood == 1
        ; Grow - don't remove tail
        inc SnakeLen
        
        mov ecx, SnakeLen
        dec ecx
        mov i, ecx
        .while i > 0
            mov eax, i
            dec eax
            shl eax, 2
            
            mov ebx, offset SnakeX
            add ebx, eax
            mov edx, [ebx]
            
            mov eax, i
            shl eax, 2
            mov ebx, offset SnakeX
            add ebx, eax
            mov [ebx], edx
            
            mov eax, i
            dec eax
            shl eax, 2
            mov ebx, offset SnakeY
            add ebx, eax
            mov edx, [ebx]
            
            mov eax, i
            shl eax, 2
            mov ebx, offset SnakeY
            add ebx, eax
            mov [ebx], edx
            
            dec i
        .endw
    .else
        ; Normal move
        mov ecx, SnakeLen
        dec ecx
        mov i, ecx
        .while i > 0
            mov eax, i
            dec eax
            shl eax, 2
            
            mov ebx, offset SnakeX
            add ebx, eax
            mov edx, [ebx]
            
            mov eax, i
            shl eax, 2
            mov ebx, offset SnakeX
            add ebx, eax
            mov [ebx], edx
            
            mov eax, i
            dec eax
            shl eax, 2
            mov ebx, offset SnakeY
            add ebx, eax
            mov edx, [ebx]
            
            mov eax, i
            shl eax, 2
            mov ebx, offset SnakeY
            add ebx, eax
            mov [ebx], edx
            
            dec i
        .endw
    .endif
    
    mov eax, newX
    mov SnakeX[0], eax
    mov eax, newY
    mov SnakeY[0], eax
    
    ret
GameLoop endp

AIGameLoop proc
    LOCAL aiIndex:DWORD
    LOCAL i:DWORD
    LOCAL j:DWORD
    LOCAL newX:DWORD
    LOCAL newY:DWORD
    LOCAL ateFood:DWORD
    LOCAL deltaX:DWORD
    LOCAL deltaY:DWORD
    LOCAL baseOffset:DWORD
    LOCAL otherAI:DWORD
    
    mov aiIndex, 0
    .while aiIndex < MAX_AI_SNAKES
        ; Check if this AI is active
        mov eax, aiIndex
        shl eax, 2
        mov ebx, offset AIActive
        add ebx, eax
        mov eax, [ebx]
        .if eax == 0
            jmp NextAI
        .endif
        
        ; Get AI snake length
        mov eax, aiIndex
        shl eax, 2
        mov ebx, offset AISnakeLen
        add ebx, eax
        mov eax, [ebx]
        .if eax == 0
            jmp NextAI
        .endif
        
        mov ateFood, 0
        
        ; Calculate base offset for this AI snake
        mov eax, aiIndex
        mov ecx, MAX_LEN
        mul ecx
        shl eax, 2
        mov baseOffset, eax
        
        ; Get current head position
        mov eax, baseOffset
        mov ebx, offset AISnakeX
        add ebx, eax
        mov eax, [ebx]
        mov newX, eax
        
        mov eax, baseOffset
        mov ebx, offset AISnakeY
        add ebx, eax
        mov eax, [ebx]
        mov newY, eax
        
        ; Calculate direction to food
        mov eax, FoodX
        sub eax, newX
        mov deltaX, eax
        
        mov eax, FoodY
        sub eax, newY
        mov deltaY, eax
        
        ; Choose direction based on larger distance
        mov eax, deltaX
        .if SDWORD PTR eax < 0
            neg eax
        .endif
        mov ecx, deltaY
        .if SDWORD PTR ecx < 0
            neg ecx
        .endif
        
        ; Get current direction
        mov edx, aiIndex
        shl edx, 2
        mov ebx, offset AIDirection
        add ebx, edx
        
        .if eax > ecx
            ; Move horizontally
            mov eax, deltaX
            .if SDWORD PTR eax > 0
                mov ecx, [ebx]
                .if ecx != DIR_LEFT
                    mov DWORD PTR [ebx], DIR_RIGHT
                .endif
            .elseif SDWORD PTR eax < 0
                mov ecx, [ebx]
                .if ecx != DIR_RIGHT
                    mov DWORD PTR [ebx], DIR_LEFT
                .endif
            .endif
        .else
            ; Move vertically
            mov eax, deltaY
            .if SDWORD PTR eax > 0
                mov ecx, [ebx]
                .if ecx != DIR_UP
                    mov DWORD PTR [ebx], DIR_DOWN
                .endif
            .elseif SDWORD PTR eax < 0
                mov ecx, [ebx]
                .if ecx != DIR_DOWN
                    mov DWORD PTR [ebx], DIR_UP
                .endif
            .endif
        .endif
        
        ; Update position based on direction
        mov eax, [ebx]
        .if eax == DIR_UP
            dec newY
        .elseif eax == DIR_DOWN
            inc newY
        .elseif eax == DIR_LEFT
            dec newX
        .elseif eax == DIR_RIGHT
            inc newX
        .endif
        
        ; Check wall collision
        mov eax, newX
        .if eax < 0
            jmp DeactivateAI
        .endif
        .if eax >= GRID_SIZE
            jmp DeactivateAI
        .endif
        
        mov eax, newY
        .if eax < 0
            jmp DeactivateAI
        .endif
        .if eax >= GRID_SIZE
            jmp DeactivateAI
        .endif
        
        ; Check collision with player snake
        mov i, 0
        mov ecx, SnakeLen
        .while i < ecx
            mov eax, i
            shl eax, 2
            mov ebx, offset SnakeX
            add ebx, eax
            mov edx, [ebx]
            
            .if edx == newX
                mov ebx, offset SnakeY
                add ebx, eax
                mov edx, [ebx]
                .if edx == newY
                    ; Player loses
                    mov bGameOver, 1
                    invoke wsprintf, addr buffer, addr szGameOver, Score
                    invoke MessageBox, hWnd, addr buffer, addr szAppName, MB_OK
                    ret
                .endif
            .endif
            
            inc i
        .endw
        
        ; Check self collision
        mov eax, aiIndex
        shl eax, 2
        mov ebx, offset AISnakeLen
        add ebx, eax
        mov ecx, [ebx]
        
        mov i, 1
        .while i < ecx
            mov eax, i
            mov edx, aiIndex
            mov ecx, MAX_LEN
            mul ecx
            add eax, edx
            mul ecx
            shl eax, 2
            
            mov ebx, offset AISnakeX
            add ebx, baseOffset
            add ebx, i
            add ebx, i
            add ebx, i
            add ebx, i
            mov edx, [ebx]
            
            .if edx == newX
                mov ebx, offset AISnakeY
                add ebx, baseOffset
                mov eax, i
                shl eax, 2
                add ebx, eax
                mov edx, [ebx]
                .if edx == newY
                    jmp DeactivateAI
                .endif
            .endif
            
            mov eax, aiIndex
            shl eax, 2
            mov ebx, offset AISnakeLen
            add ebx, eax
            mov ecx, [ebx]
            inc i
        .endw
        
        ; Check collision with other AI snakes
        mov otherAI, 0
        .while otherAI < MAX_AI_SNAKES
            mov eax, otherAI
            .if eax == aiIndex
                jmp NextOtherAI
            .endif
            
            ; Check if other AI is active
            mov eax, otherAI
            shl eax, 2
            mov ebx, offset AIActive
            add ebx, eax
            mov eax, [ebx]
            .if eax == 0
                jmp NextOtherAI
            .endif
            
            ; Get other AI length
            mov eax, otherAI
            shl eax, 2
            mov ebx, offset AISnakeLen
            add ebx, eax
            mov ecx, [ebx]
            
            ; Check collision with all segments of other AI
            mov j, 0
            .while j < ecx
                mov eax, otherAI
                mov edx, MAX_LEN
                mul edx
                add eax, j
                shl eax, 2
                
                mov ebx, offset AISnakeX
                add ebx, eax
                mov edx, [ebx]
                
                .if edx == newX
                    mov ebx, offset AISnakeY
                    add ebx, eax
                    mov edx, [ebx]
                    .if edx == newY
                        jmp DeactivateAI
                    .endif
                .endif
                
                inc j
            .endw
            
        NextOtherAI:
            inc otherAI
        .endw
        
        ; Check food
        mov eax, newX
        .if eax == FoodX
            mov eax, newY
            .if eax == FoodY
                mov ateFood, 1
                invoke GenerateFood
            .endif
        .endif
        
        ; Move AI snake
        mov eax, aiIndex
        shl eax, 2
        mov ebx, offset AISnakeLen
        add ebx, eax
        mov ecx, [ebx]
        
        .if ateFood == 1
            ; Grow
            inc DWORD PTR [ebx]
            mov ecx, [ebx]
        .endif
        
        dec ecx
        mov i, ecx
        .while i > 0
            ; Copy position from i-1 to i
            mov eax, aiIndex
            mov edx, MAX_LEN
            mul edx
            mov ecx, i
            dec ecx
            add eax, ecx
            shl eax, 2
            
            mov ebx, offset AISnakeX
            add ebx, eax
            mov edx, [ebx]
            
            mov eax, aiIndex
            push edx
            mov edx, MAX_LEN
            mul edx
            add eax, i
            shl eax, 2
            pop edx
            
            mov ebx, offset AISnakeX
            add ebx, eax
            mov [ebx], edx
            
            ; Y coordinate
            mov eax, aiIndex
            mov edx, MAX_LEN
            mul edx
            mov ecx, i
            dec ecx
            add eax, ecx
            shl eax, 2
            
            mov ebx, offset AISnakeY
            add ebx, eax
            mov edx, [ebx]
            
            mov eax, aiIndex
            push edx
            mov edx, MAX_LEN
            mul edx
            add eax, i
            shl eax, 2
            pop edx
            
            mov ebx, offset AISnakeY
            add ebx, eax
            mov [ebx], edx
            
            dec i
        .endw
        
        ; Update head
        mov eax, baseOffset
        mov ebx, offset AISnakeX
        add ebx, eax
        mov edx, newX
        mov [ebx], edx
        
        mov eax, baseOffset
        mov ebx, offset AISnakeY
        add ebx, eax
        mov edx, newY
        mov [ebx], edx
        
        jmp NextAI
        
    DeactivateAI:
        mov eax, aiIndex
        shl eax, 2
        mov ebx, offset AIActive
        add ebx, eax
        mov DWORD PTR [ebx], 0
        mov ebx, offset AISnakeLen
        add ebx, eax
        mov DWORD PTR [ebx], 0
        
    NextAI:
        inc aiIndex
    .endw
    
    ret
AIGameLoop endp


DrawGame proc hdc:DWORD
    LOCAL hBrush:DWORD
    LOCAL hPen:DWORD
    LOCAL hFont:DWORD
    LOCAL hOldFont:DWORD
    LOCAL rect:RECT
    LOCAL i:DWORD
    LOCAL level:DWORD
    LOCAL aiIndex:DWORD
    LOCAL aiHeadColor:DWORD
    LOCAL aiBodyColor:DWORD
    
    ; Calculate level based on score (every 5 points = 1 level)
    mov eax, Score
    xor edx, edx
    mov ecx, 5
    div ecx
    inc eax
    mov level, eax
    
    ; Background with better color
    invoke CreateSolidBrush, 00F0F0Fh
    mov hBrush, eax
    mov rect.left, 0
    mov rect.top, 0
    mov rect.right, WINDOW_WIDTH
    mov rect.bottom, WINDOW_HEIGHT
    invoke FillRect, hdc, addr rect, hBrush
    invoke DeleteObject, hBrush
    
    ; Game area
    invoke CreateSolidBrush, 02A2A2Ah
    mov hBrush, eax
    mov rect.left, 10
    mov rect.top, 10
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 10
    mov rect.right, eax
    mov rect.bottom, eax
    invoke FillRect, hdc, addr rect, hBrush
    invoke DeleteObject, hBrush
    
    ; Right panel background
    invoke CreateSolidBrush, 02A2A2Ah
    mov hBrush, eax
    mov rect.left, 620
    mov rect.top, 10
    mov rect.right, 780
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 10
    mov rect.bottom, eax
    invoke FillRect, hdc, addr rect, hBrush
    invoke DeleteObject, hBrush
    
    ; Border with nice color
    invoke CreatePen, PS_SOLID, 2, 00A0A0Ah
    invoke SelectObject, hdc, eax
    mov hPen, eax
    
    invoke MoveToEx, hdc, 10, 10, NULL
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 10
    push eax
    invoke LineTo, hdc, eax, 10
    pop eax
    push eax
    invoke LineTo, hdc, eax, eax
    pop eax
    push eax
    invoke LineTo, hdc, 10, eax
    invoke LineTo, hdc, 10, 10
    
    invoke SelectObject, hdc, hPen
    invoke DeleteObject, hPen
    
    ; Grid lines
    invoke CreatePen, PS_SOLID, 1, 03C3C3Ch
    invoke SelectObject, hdc, eax
    push eax
    
    mov i, 0
    .while i <= GRID_SIZE
        mov eax, i
        mov ecx, CELL_SIZE
        mul ecx
        add eax, 10
        
        invoke MoveToEx, hdc, eax, 10, NULL
        push eax
        mov eax, GRID_SIZE
        mov ecx, CELL_SIZE
        mul ecx
        add eax, 10
        mov ecx, eax
        pop eax
        invoke LineTo, hdc, eax, ecx
        
        mov eax, i
        mov ecx, CELL_SIZE
        mul ecx
        add eax, 10
        push eax
        invoke MoveToEx, hdc, 10, eax, NULL
        pop eax
        push eax
        mov ecx, GRID_SIZE
        mov eax, ecx
        mov ecx, CELL_SIZE
        mul ecx
        add eax, 10
        mov ecx, eax
        pop eax
        invoke LineTo, hdc, ecx, eax
        
        inc i
    .endw
    
    pop eax
    invoke SelectObject, hdc, eax
    invoke DeleteObject, eax
    
    ; Food with shadow
    invoke CreateSolidBrush, 08A0000h
    mov hBrush, eax
    
    mov eax, FoodX
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 14
    mov rect.left, eax
    
    mov eax, FoodY
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 14
    mov rect.top, eax
    
    mov eax, FoodX
    inc eax
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 6
    mov rect.right, eax
    
    mov eax, FoodY
    inc eax
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 6
    mov rect.bottom, eax
    
    invoke FillRect, hdc, addr rect, hBrush
    invoke DeleteObject, hBrush
    
    ; Food main
    invoke CreateSolidBrush, 00000FFh
    mov hBrush, eax
    
    mov eax, FoodX
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 13
    mov rect.left, eax
    
    mov eax, FoodY
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 13
    mov rect.top, eax
    
    mov eax, FoodX
    inc eax
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 7
    mov rect.right, eax
    
    mov eax, FoodY
    inc eax
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 7
    mov rect.bottom, eax
    
    invoke FillRect, hdc, addr rect, hBrush
    invoke DeleteObject, hBrush
    
    ; Snake
    mov i, 0
    mov ecx, SnakeLen
    .while i < ecx
        .if i == 0
            mov eax, SnakeHeadColor
            invoke CreateSolidBrush, eax
        .else
            mov eax, SnakeBodyColor
            invoke CreateSolidBrush, eax
        .endif
        mov hBrush, eax
        
        mov eax, i
        shl eax, 2
        mov ebx, offset SnakeX
        add ebx, eax
        mov edx, [ebx]
        mov ecx, CELL_SIZE
        mov eax, edx
        mul ecx
        add eax, 13
        mov rect.left, eax
        
        mov eax, i
        shl eax, 2
        mov ebx, offset SnakeY
        add ebx, eax
        mov edx, [ebx]
        mov ecx, CELL_SIZE
        mov eax, edx
        mul ecx
        add eax, 13
        mov rect.top, eax
        
        mov eax, i
        shl eax, 2
        mov ebx, offset SnakeX
        add ebx, eax
        mov edx, [ebx]
        inc edx
        mov ecx, CELL_SIZE
        mov eax, edx
        mul ecx
        add eax, 7
        mov rect.right, eax
        
        mov eax, i
        shl eax, 2
        mov ebx, offset SnakeY
        add ebx, eax
        mov edx, [ebx]
        inc edx
        mov ecx, CELL_SIZE
        mov eax, edx
        mul ecx
        add eax, 7
        mov rect.bottom, eax
        
        invoke FillRect, hdc, addr rect, hBrush
        invoke DeleteObject, hBrush
        
        inc i
        mov ecx, SnakeLen
    .endw
    
    ; Draw AI Snakes
    .if AIEnabled == 1
        mov aiIndex, 0
        .while aiIndex < MAX_AI_SNAKES
            ; Check if this AI is active
            mov eax, aiIndex
            shl eax, 2
            mov ebx, offset AIActive
            add ebx, eax
            mov eax, [ebx]
            .if eax == 0
                jmp NextAIDraw
            .endif
            
            ; Get AI snake length
            mov eax, aiIndex
            shl eax, 2
            mov ebx, offset AISnakeLen
            add ebx, eax
            mov ecx, [ebx]
            .if ecx == 0
                jmp NextAIDraw
            .endif
            
            ; Set color based on AI index
            .if aiIndex == 0
                mov aiHeadColor, 00000FFh    ; Red
                mov aiBodyColor, 000008Ah    ; Dark red
            .elseif aiIndex == 1
                mov aiHeadColor, 000AAFFh    ; Orange
                mov aiBodyColor, 0005588h    ; Dark orange
            .else
                mov aiHeadColor, 0FF00FFh    ; Magenta
                mov aiBodyColor, 0880088h    ; Dark magenta
            .endif
            
            mov i, 0
            .while i < ecx
                .if i == 0
                    mov eax, aiHeadColor
                    invoke CreateSolidBrush, eax
                .else
                    mov eax, aiBodyColor
                    invoke CreateSolidBrush, eax
                .endif
                mov hBrush, eax
                
                mov eax, aiIndex
                mov edx, MAX_LEN
                mul edx
                add eax, i
                shl eax, 2
                
                mov ebx, offset AISnakeX
                add ebx, eax
                mov edx, [ebx]
                mov ecx, CELL_SIZE
                mov eax, edx
                mul ecx
                add eax, 13
                mov rect.left, eax
                
                mov eax, aiIndex
                mov edx, MAX_LEN
                mul edx
                add eax, i
                shl eax, 2
                
                mov ebx, offset AISnakeY
                add ebx, eax
                mov edx, [ebx]
                mov ecx, CELL_SIZE
                mov eax, edx
                mul ecx
                add eax, 13
                mov rect.top, eax
                
                mov eax, aiIndex
                mov edx, MAX_LEN
                mul edx
                add eax, i
                shl eax, 2
                
                mov ebx, offset AISnakeX
                add ebx, eax
                mov edx, [ebx]
                inc edx
                mov ecx, CELL_SIZE
                mov eax, edx
                mul ecx
                add eax, 7
                mov rect.right, eax
                
                mov eax, aiIndex
                mov edx, MAX_LEN
                mul edx
                add eax, i
                shl eax, 2
                
                mov ebx, offset AISnakeY
                add ebx, eax
                mov edx, [ebx]
                inc edx
                mov ecx, CELL_SIZE
                mov eax, edx
                mul ecx
                add eax, 7
                mov rect.bottom, eax
                
                invoke FillRect, hdc, addr rect, hBrush
                invoke DeleteObject, hBrush
                
                inc i
                mov eax, aiIndex
                shl eax, 2
                mov ebx, offset AISnakeLen
                add ebx, eax
                mov ecx, [ebx]
            .endw
            
        NextAIDraw:
            inc aiIndex
        .endw
    .endif
    
    ; Info bar
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 20
    mov rect.top, eax
    mov rect.left, 10
    add eax, 80
    mov rect.bottom, eax
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 10
    mov rect.right, eax
    
    invoke CreateSolidBrush, 03A3A3Ah
    mov hBrush, eax
    invoke FillRect, hdc, addr rect, hBrush
    invoke DeleteObject, hBrush
    
    ; Score
    invoke CreateFont, 22, 0, 0, 0, FW_BOLD, 0, 0, 0,
           DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
           DEFAULT_QUALITY, DEFAULT_PITCH or FF_DONTCARE, NULL
    mov hFont, eax
    invoke SelectObject, hdc, hFont
    mov hOldFont, eax
    
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 32
    mov rect.top, eax
    mov rect.left, 20
    add eax, 32
    mov rect.bottom, eax
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    mov rect.right, eax
    
    invoke SetBkMode, hdc, TRANSPARENT
    invoke SetTextColor, hdc, 000FFFFh
    
    invoke wsprintf, addr buffer, addr szScore, Score, level, SnakeLen
    invoke DrawText, hdc, addr buffer, -1, addr rect, DT_LEFT
    
    ; Controls info
    invoke SelectObject, hdc, hOldFont
    invoke DeleteObject, hFont
    
    invoke CreateFont, 15, 0, 0, 0, FW_NORMAL, 0, 0, 0,
           DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
           DEFAULT_QUALITY, DEFAULT_PITCH or FF_DONTCARE, NULL
    mov hFont, eax
    invoke SelectObject, hdc, hFont
    
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    add eax, 66
    mov rect.top, eax
    mov rect.left, 20
    add eax, 25
    mov rect.bottom, eax
    mov eax, GRID_SIZE
    mov ecx, CELL_SIZE
    mul ecx
    mov rect.right, eax
    
    invoke SetTextColor, hdc, 00CCCCCCh
    invoke DrawText, hdc, addr szControls, -1, addr rect, DT_LEFT
    
    ; Right panel labels
    invoke CreateFont, 18, 0, 0, 0, FW_BOLD, 0, 0, 0,
           DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
           DEFAULT_QUALITY, DEFAULT_PITCH or FF_DONTCARE, NULL
    invoke SelectObject, hdc, hFont
    invoke DeleteObject, hFont
    mov hFont, eax
    
    mov rect.left, 630
    mov rect.top, 120
    mov rect.right, 770
    mov rect.bottom, 145
    invoke SetTextColor, hdc, 000DDDDh
    invoke DrawText, hdc, addr szColorInfo, -1, addr rect, DT_LEFT
    
    ; Best score on right panel
    mov rect.left, 630
    mov rect.top, 320
    mov rect.right, 770
    mov rect.bottom, 345
    invoke SetTextColor, hdc, 000FFh
    invoke wsprintf, addr buffer, addr szHighScoreInfo, HighScore
    invoke DrawText, hdc, addr buffer, -1, addr rect, DT_LEFT
    
    ; Paused
    .if bPaused == 1
        invoke SelectObject, hdc, hOldFont
        invoke DeleteObject, hFont
        
        invoke CreateFont, 44, 0, 0, 0, FW_BOLD, 0, 0, 0,
               DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
               DEFAULT_QUALITY, DEFAULT_PITCH or FF_DONTCARE, NULL
        mov hFont, eax
        invoke SelectObject, hdc, hFont
        
        mov eax, GRID_SIZE
        mov ecx, CELL_SIZE
        mul ecx
        shr eax, 1
        sub eax, 110
        mov rect.left, eax
        mov eax, GRID_SIZE
        mov ecx, CELL_SIZE
        mul ecx
        shr eax, 1
        sub eax, 22
        mov rect.top, eax
        add eax, 44
        mov rect.bottom, eax
        mov eax, GRID_SIZE
        mov ecx, CELL_SIZE
        mul ecx
        shr eax, 1
        add eax, 110
        mov rect.right, eax
        
        invoke SetTextColor, hdc, 000FFFFh
        invoke DrawText, hdc, addr szPaused, -1, addr rect, DT_CENTER
    .endif
    
    invoke SelectObject, hdc, hOldFont
    invoke DeleteObject, hFont
    
    ret
DrawGame endp

LoadHighScore proc
    LOCAL hFile:DWORD
    LOCAL bytesRead:DWORD
    
    invoke CreateFile, addr szFileName, GENERIC_READ, 0, NULL, 
           OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL
    .if eax != INVALID_HANDLE_VALUE
        mov hFile, eax
        invoke ReadFile, hFile, addr HighScore, 4, addr bytesRead, NULL
        invoke CloseHandle, hFile
    .else
        mov HighScore, 0
    .endif
    ret
LoadHighScore endp

SaveHighScore proc
    LOCAL hFile:DWORD
    LOCAL bytesWritten:DWORD
    
    invoke CreateFile, addr szFileName, GENERIC_WRITE, 0, NULL,
           CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL
    .if eax != INVALID_HANDLE_VALUE
        mov hFile, eax
        invoke WriteFile, hFile, addr HighScore, 4, addr bytesWritten, NULL
        invoke CloseHandle, hFile
    .endif
    ret
SaveHighScore endp

end start
