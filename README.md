# usv_ws 总管理仓库

Updated: 2026-04-13T13:01:44Z

## 1. 目标
本仓库只负责 `usv_ws` 工作区的总管理入口，不直接纳入以下外部源码仓库的版本历史：
- `ardupilot-usv/`
- `WQ-USV-QGroundControl/`
- `src/usv_ros/`

根仓库保留：
- `docs/current/` 技术文档
- `bootstrap_workspace.sh`
- `bootstrap_workspace.ps1`
- `.gitignore`

## 2. 获取总管理仓库
```bash
git clone <your-usv-ws-manager-repo-url> usv_ws
cd usv_ws
```

## 3. Bootstrap 外部源码仓库
### 3.1 Bash / WSL / Linux
```bash
./bootstrap_workspace.sh <ardupilot_url> <qgc_url> <usv_ros_url>
```

使用环境变量：
```bash
ARDUPILOT_URL=<ardupilot_url> \
QGC_URL=<qgc_url> \
USV_ROS_URL=<usv_ros_url> \
./bootstrap_workspace.sh
```

可选固定版本：
```bash
ARDUPILOT_REF=<branch|tag|commit> \
QGC_REF=<branch|tag|commit> \
USV_ROS_REF=<branch|tag|commit> \
./bootstrap_workspace.sh <ardupilot_url> <qgc_url> <usv_ros_url>
```

### 3.2 Windows PowerShell
```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap_workspace.ps1 <ardupilot_url> <qgc_url> <usv_ros_url>
```

使用环境变量：
```powershell
$env:ARDUPILOT_URL = '<ardupilot_url>'
$env:QGC_URL = '<qgc_url>'
$env:USV_ROS_URL = '<usv_ros_url>'
.\bootstrap_workspace.ps1
```

可选固定版本：
```powershell
$env:ARDUPILOT_REF = '<branch|tag|commit>'
$env:QGC_REF = '<branch|tag|commit>'
$env:USV_ROS_REF = '<branch|tag|commit>'
.\bootstrap_workspace.ps1
```

## 4. Bootstrap 后目录结构
```text
usv_ws/
├─ .gitignore
├─ bootstrap_workspace.sh
├─ bootstrap_workspace.ps1
├─ docs/
├─ ardupilot-usv/
├─ WQ-USV-QGroundControl/
└─ src/
   └─ usv_ros/
```

## 5. 三端构建入口
### 5.1 ROS 工作区
依据：`src/usv_ros/README.md L128-L130`
```bash
cd ~/usv_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

### 5.2 QGroundControl
依据：`WQ-USV-QGroundControl/Makefile L49-L69`、`WQ-USV-QGroundControl/justfile L24-L56`
```bash
cd ~/usv_ws/WQ-USV-QGroundControl
make submodules
make configure
make build
```

### 5.3 ArduPilot 固件
依据：`docs/current/ardupilot_firmware_guide.md L42-L49`
```bash
wsl
cd /mnt/d/usv_ws/ardupilot-usv
git submodule update --init --recursive
./waf configure --board Pixhawk6C
./waf rover
```

## 6. Git 管理策略
根仓库 `.gitignore` 默认忽略：
- `/ardupilot-usv/`
- `/WQ-USV-QGroundControl/`
- `/src/usv_ros/`
- `/build/`
- `/devel/`
- `/log/`
- `/.usv_run/`
- `/ardurover.apj`

因此根仓库可单独执行：
```bash
git init
git add .
git commit -m "Feat: add workspace bootstrap entry"
```

## 7. 约束
- 本仓库不内置三方源码仓库远端 URL，执行 bootstrap 时必须显式传入。
- `ardupilot-usv` 固件构建环境为 WSL Ubuntu。
- PowerShell 脚本负责 clone/bootstrap，不替代 ROS/QGC/固件各自仓库内的原生构建流程。
