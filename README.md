# usv_ws 总管理仓库

Updated: 2026-04-13T13:34:06Z

## 1. 目标
本仓库只负责 `usv_ws` 工作区的总管理入口，不直接纳入以下外部源码仓库的版本历史：
- `ardupilot-usv/`
- `WQ-USV-QGroundControl/`
- `src/usv_ros/`

根仓库保留：
- `docs/current/` 技术文档
- `bootstrap_workspace.bat`
- `.gitignore`

## 2. 获取总管理仓库
```bash
git clone https://github.com/MIGO-OvO/usv_ws.git usv_ws
cd usv_ws
```

## 3. Bootstrap 外部源码仓库
仅保留 Windows 批处理入口：
```bat
bootstrap_workspace.bat
```

脚本内置仓库地址：
- `https://github.com/MIGO-OvO/ardupilot-usv.git`
- `https://github.com/MIGO-OvO/WQ-USV-QGroundControl.git`
- `https://github.com/MIGO-OvO/usv_ros.git`

## 4. Bootstrap 后目录结构
```text
usv_ws/
├─ .gitignore
├─ README.md
├─ bootstrap_workspace.bat
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
- `/src/CMakeLists.txt`
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
- 本仓库只保留 `bootstrap_workspace.bat` 一个 Windows 入口脚本。
- `.bat` 已写死 3 个外部源码仓库地址，不再要求执行时传入 URL。
- `ardupilot-usv` 固件构建环境为 WSL Ubuntu。
- 批处理脚本只负责 clone/bootstrap；ROS/QGC/ArduPilot 仍按各自仓库原生构建入口执行。
