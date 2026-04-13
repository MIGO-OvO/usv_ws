param(
    [string]$ArduPilotUrl = $env:ARDUPILOT_URL,
    [string]$QgcUrl = $env:QGC_URL,
    [string]$UsvRosUrl = $env:USV_ROS_URL,
    [string]$ArduPilotRef = $env:ARDUPILOT_REF,
    [string]$QgcRef = $env:QGC_REF,
    [string]$UsvRosRef = $env:USV_ROS_REF
)

$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $RootDir 'src'
$ArduPilotDir = Join-Path $RootDir 'ardupilot-usv'
$QgcDir = Join-Path $RootDir 'WQ-USV-QGroundControl'
$UsvRosDir = Join-Path $SrcDir 'usv_ros'

function Write-Log {
    param([string]$Message)
    Write-Host "[workspace-bootstrap] $Message"
}

function Show-Usage {
    @"
用途: 在 usv_ws 根目录拉取外部源码仓库，保留当前仓库作为总管理入口。

用法:
  powershell -ExecutionPolicy Bypass -File .\bootstrap_workspace.ps1 <ardupilot_url> <qgc_url> <usv_ros_url>

也可使用环境变量:
  `$env:ARDUPILOT_URL='...'
  `$env:QGC_URL='...'
  `$env:USV_ROS_URL='...'
  .\bootstrap_workspace.ps1

可选环境变量:
  ARDUPILOT_REF=<branch|tag|commit>
  QGC_REF=<branch|tag|commit>
  USV_ROS_REF=<branch|tag|commit>

目标目录:
  ardupilot-usv\
  WQ-USV-QGroundControl\
  src\usv_ros\
"@ | Write-Host
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "缺少命令: $Name"
    }
}

function Require-RepoUrl {
    param(
        [string]$Name,
        [string]$Url
    )
    if ([string]::IsNullOrWhiteSpace($Url)) {
        Write-Log "缺少 $Name 仓库地址"
        Show-Usage
        throw "参数不足"
    }
}

function Invoke-Git {
    param([string[]]$Args)
    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git 命令失败: git $($Args -join ' ')"
    }
}

function Clone-Repo {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Dir,
        [string]$Ref
    )

    $GitDir = Join-Path $Dir '.git'
    if (Test-Path $GitDir) {
        Write-Log "已存在 ${Name}: $Dir"
    } elseif (Test-Path $Dir) {
        throw "目标路径已存在但不是 Git 仓库: $Dir"
    } else {
        Write-Log "克隆 ${Name}: $Url -> $Dir"
        Invoke-Git @('clone', '--recursive', $Url, $Dir)
    }

    if (-not [string]::IsNullOrWhiteSpace($Ref)) {
        Write-Log "切换 ${Name} 到 $Ref"
        Invoke-Git @('-C', $Dir, 'fetch', '--all', '--tags')
        Invoke-Git @('-C', $Dir, 'checkout', $Ref)
    }

    Write-Log "同步 ${Name} 子模块"
    Invoke-Git @('-C', $Dir, 'submodule', 'update', '--init', '--recursive')
}

function Print-NextSteps {
    @"

后续建议命令:
1. ROS 工作区 (PowerShell / WSL)
   Set-Location "$RootDir"
   rosdep install --from-paths src --ignore-src -r -y
   catkin_make
   . devel/setup.bash

2. QGroundControl
   Set-Location "$QgcDir"
   make submodules
   make configure
   make build

3. ArduPilot (WSL Ubuntu)
   Set-Location "$ArduPilotDir"
   ./waf configure --board Pixhawk6C
   ./waf rover
"@ | Write-Host
}

Require-Command 'git'
Require-RepoUrl 'ardupilot-usv' $ArduPilotUrl
Require-RepoUrl 'WQ-USV-QGroundControl' $QgcUrl
Require-RepoUrl 'usv_ros' $UsvRosUrl

New-Item -ItemType Directory -Force -Path $SrcDir | Out-Null

Clone-Repo 'ardupilot-usv' $ArduPilotUrl $ArduPilotDir $ArduPilotRef
Clone-Repo 'WQ-USV-QGroundControl' $QgcUrl $QgcDir $QgcRef
Clone-Repo 'usv_ros' $UsvRosUrl $UsvRosDir $UsvRosRef

Write-Log '工作区源码目录已就位'
Print-NextSteps
