@echo off
rem Camoufox 逆向控制台入口 —— 双击本文件即可打开菜单。
setlocal
set "PS=pwsh"
where pwsh >nul 2>nul || set "PS=powershell"
"%PS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0bin\console.ps1"
endlocal
