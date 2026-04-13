@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
set "SRC_DIR=%ROOT_DIR%\src"
set "ARDUPILOT_DIR=%ROOT_DIR%\ardupilot-usv"
set "QGC_DIR=%ROOT_DIR%\WQ-USV-QGroundControl"
set "USV_ROS_DIR=%SRC_DIR%\usv_ros"

set "ARDUPILOT_URL=https://github.com/MIGO-OvO/ardupilot-usv.git"
set "QGC_URL=https://github.com/MIGO-OvO/WQ-USV-QGroundControl.git"
set "USV_ROS_URL=https://github.com/MIGO-OvO/usv_ros.git"

echo [workspace-bootstrap] ROOT=%ROOT_DIR%
where git >nul 2>nul || (
  echo [workspace-bootstrap] 缺少命令: git
  exit /b 1
)

if not exist "%SRC_DIR%" mkdir "%SRC_DIR%"

call :clone_repo ardupilot-usv "%ARDUPILOT_URL%" "%ARDUPILOT_DIR%" || exit /b 1
call :clone_repo WQ-USV-QGroundControl "%QGC_URL%" "%QGC_DIR%" || exit /b 1
call :clone_repo usv_ros "%USV_ROS_URL%" "%USV_ROS_DIR%" || exit /b 1

echo [workspace-bootstrap] 工作区源码目录已就位
echo.
echo 后续建议命令:
echo 1. ROS 工作区
echo    cd /d "%ROOT_DIR%"
echo    rosdep install --from-paths src --ignore-src -r -y
echo    catkin_make
echo.
echo 2. QGroundControl
echo    cd /d "%QGC_DIR%"
echo    make submodules
echo    make configure
echo    make build
echo.
echo 3. ArduPilot ^(WSL Ubuntu^)
echo    wsl
echo    cd /mnt/d/usv_ws/ardupilot-usv
echo    git submodule update --init --recursive
echo    ./waf configure --board Pixhawk6C
echo    ./waf rover
exit /b 0

:clone_repo
set "NAME=%~1"
set "URL=%~2"
set "DIR=%~3"
if exist "%DIR%\.git" (
  echo [workspace-bootstrap] 已存在 %NAME%: %DIR%
) else if exist "%DIR%" (
  echo [workspace-bootstrap] 目标路径已存在但不是 Git 仓库: %DIR%
  exit /b 1
) else (
  echo [workspace-bootstrap] 克隆 %NAME%: %URL% -^> %DIR%
  git clone --recursive "%URL%" "%DIR%" || exit /b 1
)
git -C "%DIR%" submodule update --init --recursive || exit /b 1
exit /b 0
