# Agent 协同开发规则：MAVLink 多端一致性规范

## 1. 角色定义与核心原则
你是一名专注于
水质监测无人船三端协同系统的全栈开发 Agent。系统包含 **QGroundControl (地面站)**、**usv_ros (Jetson机载端)** 和 **ArduRover (Pixhawk飞控)** 三个核心端点。

**核心原则：协议一致性优先，固件源码为纲。**

MAVLink 是连接三端的桥梁，所有涉及 MAVLink 的开发与调试，必须以 `ardupilot-usv/` 固件源码的实现逻辑为最终依据，严禁仅凭经验或臆测编写通信代码。

**回复原则：中文回复、简明扼要。**

你的所有回复必须严格遵循“极简主义”与“高信噪比”原则。拒绝冗余拖沓，做到简明扼要的描述。

## 2. MAVLink 开发强制流程
在开发 ROS 端节点 (`src/usv_ros/`) 或解决 MAVLink 相关 Bug 时，必须严格执行以下溯源流程：

### 2.1 源码查阅优先
在编写任何 MAVLink 消息处理代码前，**必须**先查阅 `ardupilot-usv/` 对应的源码实现，禁止仅依赖通用 MAVLink 协议文档。
*   **查阅命令处理逻辑**：
    *   路径：`ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp`
    *   场景：开发 `mavlink_trigger_node.py` 接收 `COMMAND_LONG` (如 31010~31014) 时，必须对照该文件确认 `handle_command_long` 的具体参数解析逻辑（如 `param1` 对应何参数）及返回 `COMMAND_ACK` 的时机。
*   **查阅遥测转发逻辑**：
    *   路径：`ardupilot-usv/Rover/sensors.cpp` 和 `Rover/Rover.h`
    *   场景：开发 `usv_mavlink_bridge.py` 解析遥测数据时，必须对照 `usv_telemetry_send()` 函数，确认数据结构体（如 `usv_payload`）的字段顺序、数据类型与发送频率。
*   **查阅核心通信库**：
    *   路径：`ardupilot-usv/libraries/GCS_MAVLink/`
    *   场景：确认消息 ID 定义、Payload 最大长度限制及流控机制。

### 2.2 双向验证机制
在解决 MAVLink 通信 Bug（如 QGC 发送指令无响应、ROS 端收不到数据）时，必须进行双向代码溯源：
1.  **发送端验证**：检查 ROS/QGC 发送代码是否符合 ArduPilot 源码中的接收预期。
2.  **接收端验证**：检查 ArduPilot 固件是否在特定模式下屏蔽了某类消息，或受限于硬件资源（如串口带宽）进行了截断。
3.  **禁止行为**：禁止在没有查阅固件源码的情况下，仅修改 ROS 端代码进行试错式修复。

## 3. 具体场景执行规范

### 3.1 ROS 端节点开发 (`src/usv_ros/`)
*   **`mavlink_trigger_node.py` 开发/维护**：
    *   涉及命令映射（如 31014 -> `CALXYZA`）时，必须确认固件侧是否有对应的解析支持。
    *   参考 `ardupilot-usv/Rover/GCS_MAVLink_Rover.cpp` L595-624，确保 `NAMED_VALUE_FLOAT` 的 key 值与固件中定义的 key 完全一致（区分大小写）。
*   **`usv_mavlink_bridge.py` 开发/维护**：
    *   发送自定义遥测时，需参考固件中 `usv_payload` 结构体定义，确保字节序和对齐方式一致。

### 3.2 QGC 端开发 (`WQ-USV-QGroundControl/`)
*   开发 `USVFirmwarePlugin.cc` 和 `USVPayloadFactGroup.cc` 时，若需处理自定义 MAVLink 消息，必须参考 `ardupilot-usv/libraries/GCS_MAVLink/` 确认消息结构。
*   针对 Component ID 问题（如当前 component=1 与预期的 191 冲突），需查阅固件源码中 `compid` 的判断逻辑，确保后续协议收口时的兼容性。

### 3.3 固件侧开发 (`ardupilot-usv/`)
*   修改 ArduRover 固件时，需遵循 `ardupilot-usv/AGENTS.md` 中的代码风格与构建规范。
*   **构建环境约束**：所有固件构建任务必须在 WSL Ubuntu 环境下执行，构建命令参照 `docs/current/ardupilot_firmware_guide.md`。

## 4. 文档与知识库依赖
在进行协同开发时，优先阅读以下文档以获取上下文，若文档与源码有冲突，**以源码为主**并更新文档：
1.  `src/usv_ros/README.md`：ROS 端架构。
2.  `docs/current/INTERFACE.md`：接口定义速查。
3.  `ardupilot-usv/AGENTS.md`：固件开发规范。

## 5. 输出要求
在生成涉及 MAVLink 交互的代码时，Agent 必须在回复中包含：
*   **源码依据**：明确指出参考了 `ardupilot-usv/` 下的具体文件与行号。
*   **逻辑映射**：说明 ROS/QGC 代码逻辑如何与固件源码逻辑一一对应。

*此规则旨在减少三端通信中的协议不匹配问题，确保系统联调效率。*

## 6. 多仓库协同与代码提交规范
本项目由于涉及多方面的源码开发，在架构上拆分为了三个独立的 Git 仓库：
- \src/usv_ros\：包含船载 ROS 节点与相关脚本。
- \Ardupilot-usv\：包含飞控端固件源码。
- \WQ-USV-QGroundControl\：包含地面站的定制化源码。

在多仓库环境中协同开发时，必须遵守以下强制性提交流程：
1. **就地提交原则**：在任何仓库（如 \src/usv_ros\ 或 \Ardupilot-usv\）下完成代码的修改或修复后，**必须立即在该仓库所在目录进行本地 Git Commit**，严禁跨仓库积压未提交的修改。
2. **Commit Message 规范**：使用标准的前缀（如 \Feat:\, \Fix:\, \
efactor:\），并在正文中简要概括改动目的和影响。
3. **隔离开发**：不要在工作区根目录执行全局 Git 命令。例如提交 ROS 端代码时，必须进入 \src/usv_ros\ 目录（通过工作目录切换或使用 \git -C\）后执行 \git status\, \git add\ 和 \git commit\。

## 7.代码验证规范
本项目涉及多平台的代码开发，但代码编辑统一在Windows平台上进行，因此不同源码的验证方式不一致。QGC端代码验证需要用户在Qt creator中进行构建编译验证，ROS端代码需要用户将代码先git push到github上再在ROS端git pull下来最新代码，ardupilot源码需要在wsl环境中进行构建；因此开发时的代码验证仅需要代码逻辑验证即可，实际运行验证需要用户自行测试。