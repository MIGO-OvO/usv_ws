@echo off
setlocal
REM Interactive download entry; implementation belongs to the ROS repository.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0src\usv_ros\scripts\download_jetson_logs.ps1"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
