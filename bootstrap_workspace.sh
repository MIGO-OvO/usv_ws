#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$ROOT_DIR/src"

ARDUPILOT_DIR="$ROOT_DIR/ardupilot-usv"
QGC_DIR="$ROOT_DIR/WQ-USV-QGroundControl"
USV_ROS_DIR="$SRC_DIR/usv_ros"

ARDUPILOT_URL="${ARDUPILOT_URL:-${1:-}}"
QGC_URL="${QGC_URL:-${2:-}}"
USV_ROS_URL="${USV_ROS_URL:-${3:-}}"

ARDUPILOT_REF="${ARDUPILOT_REF:-}"
QGC_REF="${QGC_REF:-}"
USV_ROS_REF="${USV_ROS_REF:-}"

usage() {
    cat <<'EOF'
用途: 在 usv_ws 根目录拉取外部源码仓库，保留当前仓库作为总管理入口。

用法:
  ./bootstrap_workspace.sh <ardupilot_url> <qgc_url> <usv_ros_url>

也可使用环境变量:
  ARDUPILOT_URL=... QGC_URL=... USV_ROS_URL=... ./bootstrap_workspace.sh

可选环境变量:
  ARDUPILOT_REF=<branch|tag|commit>
  QGC_REF=<branch|tag|commit>
  USV_ROS_REF=<branch|tag|commit>

目标目录:
  ardupilot-usv/
  WQ-USV-QGroundControl/
  src/usv_ros/
EOF
}

log() {
    echo "[workspace-bootstrap] $*"
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log "缺少命令: $1"
        exit 1
    fi
}

require_repo_url() {
    local name="$1"
    local url="$2"
    if [[ -z "$url" ]]; then
        log "缺少 ${name} 仓库地址"
        usage
        exit 1
    fi
}

clone_repo() {
    local name="$1"
    local url="$2"
    local dir="$3"
    local ref="$4"

    if [[ -d "$dir/.git" ]]; then
        log "已存在 ${name}: $dir"
    elif [[ -e "$dir" ]]; then
        log "目标路径已存在但不是 Git 仓库: $dir"
        exit 1
    else
        log "克隆 ${name}: $url -> $dir"
        git clone --recursive "$url" "$dir"
    fi

    if [[ -n "$ref" ]]; then
        log "切换 ${name} 到 ${ref}"
        git -C "$dir" fetch --all --tags
        git -C "$dir" checkout "$ref"
    fi

    log "同步 ${name} 子模块"
    git -C "$dir" submodule update --init --recursive
}

print_next_steps() {
    cat <<EOF

后续建议命令:
1. ROS 工作区
   cd "$ROOT_DIR"
   rosdep install --from-paths src --ignore-src -r -y
   catkin_make
   source devel/setup.bash

2. QGroundControl
   cd "$QGC_DIR"
   make submodules
   make configure
   make build

3. ArduPilot (WSL Ubuntu)
   cd "$ARDUPILOT_DIR"
   ./waf configure --board Pixhawk6C
   ./waf rover
EOF
}

main() {
    require_cmd git
    require_repo_url "ardupilot-usv" "$ARDUPILOT_URL"
    require_repo_url "WQ-USV-QGroundControl" "$QGC_URL"
    require_repo_url "usv_ros" "$USV_ROS_URL"

    mkdir -p "$SRC_DIR"

    clone_repo "ardupilot-usv" "$ARDUPILOT_URL" "$ARDUPILOT_DIR" "$ARDUPILOT_REF"
    clone_repo "WQ-USV-QGroundControl" "$QGC_URL" "$QGC_DIR" "$QGC_REF"
    clone_repo "usv_ros" "$USV_ROS_URL" "$USV_ROS_DIR" "$USV_ROS_REF"

    log "工作区源码目录已就位"
    print_next_steps
}

main "$@"
