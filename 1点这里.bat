@echo off
setlocal enabledelayedexpansion

REM 设置当前目录为批处理文件所在目录
CD /D "%~dp0"
REM 设置窗口标题
TITLE 【Fhoe-Rail】

REM 调整控制台窗口大小
mode con cols=85 lines=40

REM 检查并获取管理员权限
>nul 2>&1 REG.exe query "HKU\S-1-5-19" || (
    ECHO Set UAC = CreateObject^("Shell.Application"^) > "%TEMP%\Getadmin.vbs"
    ECHO UAC.ShellExecute "%~f0", "%1", "", "runas", 1 >> "%TEMP%\Getadmin.vbs"
    "%TEMP%\Getadmin.vbs"
    DEL /f /q "%TEMP%\Getadmin.vbs" 2>NUL
    Exit /b
)

:continue

REM 初始化变量
set "OPTION="

echo.
echo   本程序为开源项目魔改分支，与远程桌面教程相同作者
echo.
echo   本程序禁止在闲鱼、转转等二手平台贩售（包括以安装技术费等名义）如有发现后果自负
echo.
echo   想卖东西自己写啊，拿别人的东西说是自己写的合适吗？
echo.
echo   使用本程序有50%的概率被封号，如您执意运行，代表您同意相关风险由您自己承担
echo.
echo   请输入选项：
echo.
echo   [1] 首次运行
echo.
echo   [2] 速启（默认1-1，无操作会自动选择）
echo.
echo   [3] 地图（选择具体地图）
echo.
echo   [4] 配置（配置后选地图）
echo.
echo   [5] 录制
echo.
echo   [6] 测试（测图用,F8暂停）
echo.

REM 等待用户输入或超时
choice /C 123456 /T 30 /D 2 /N >nul

REM 处理用户输入
if errorlevel 6 (
    color 0C
    echo.
    echo   Tips：按F8暂停，暂停后按F8继续，按F9重新运行当前地图
    python -i -X utf8 Honkai_Star_Rail.py --dev
    echo.
    pause
    goto :end
) else if errorlevel 5 (
    color 0B
    echo.
    python -i -X utf8 utils/record.py
    echo.
    pause
    goto :end
) else if errorlevel 4 (
    color 0D
    echo.
    python -i -X utf8 Honkai_Star_Rail.py --config
    echo.
    pause
    goto :end
) else if errorlevel 3 (
    color 0E
    echo.
    echo   正在启动程序...
    echo.
    python -i -X utf8 Honkai_Star_Rail.py --debug
    echo.
    pause
    goto :end
) else if errorlevel 2 (
    color 0F
    echo.
    echo   正在极速启动...
    echo.
    python -i -X utf8 Honkai_Star_Rail.py
    echo.
    pause
    goto :end
) else (
    color 0A
    echo.
    echo   正在检查并安装依赖...
    echo.
    python utils/install_requirements.py
    echo.
    goto :start_script
)

:start_script
echo.
echo   正在启动地图选项...
echo.
python -i -X utf8 Honkai_Star_Rail.py --debug
echo.
pause
goto :end

:end