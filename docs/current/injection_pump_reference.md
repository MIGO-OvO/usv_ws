# 进样泵功能参考
Updated: 2026-03-18T10:00:00Z

## 1. 参考来源
- `reference/MotorControlApp_Pyside6/src/ui/main_window_complete.py L631-L647`
- `reference/MotorControlApp_Pyside6/src/ui/main_window_complete.py L842-L859`
- `reference/MotorControlApp_Pyside6/lowerDevice/src/main.cpp L311-L328`
- `reference/MotorControlApp_Pyside6/lowerDevice/src/main.cpp L432-L467`
- `src/usv_ros/scripts/pump_control_node.py L420-L545`
- `src/usv_ros/scripts/web_config_server.py L860-L922`
- `src/usv_ros/frontend/src/store.ts`
- `src/usv_ros/frontend/src/components/injection-pump-card.tsx`

## 2. 协议事实
### 下位机协议
- 指令：`PUMP:ON` `PUMP:OFF` `PUMP:SPD:<0-100>` `PUMP:SET:<0-100>` `PUMP:STATUS`
- 响应：`PUMP_OK:ON,SPD=<n>` `PUMP_OK:OFF` `PUMP_OK:SPD=<n>` `PUMP_OK:SET=<n>,ON|OFF` `PUMP_STATUS:ON|OFF,SPD=<n>` `PUMP_ERR:*`
- 控制语义：进样泵为 PWM 速度执行器，不进入角度/PID 闭环。

## 3. 当前 ROS 落地状态
### pump_control_node.py
- 已发布：`/usv/injection_pump_status`
- 已提供服务：`/usv/injection_pump_on` `/usv/injection_pump_off` `/usv/injection_pump_get_status`
- 已支持：
  - `/usv/pump_command` 直通 `PUMP:*`
  - 自动化步骤 `step.pump.enable` / `step.pump.speed` / `step.pump.duration_ms`
  - `PUMP_OK/PUMP_STATUS/PUMP_ERR` 文本解析
  - 电机指令与进样泵指令间 150ms 延迟（`auto_injection_command_delay`）
  - 进样泵首发失败后单次重试（`auto_injection_retry_delay`=200ms）
  - `_wait_for_automation_step()` 中等待 `duration_ms` 后自动关闭进样泵
- 当前状态字段：`enabled` `speed` `last_response` `last_error`

### web_config_server.py
- 已提供：`/api/injection-pump/status|on|off|set`
- 已推送 Socket.IO：`injection_pump_status`

### 前端
- `Monitor.tsx`：显示进样泵状态卡片
- `Automation.tsx`：显示进样泵控制卡片与步骤配置
- `store.ts`：已接入 REST 调用与 Socket.IO 状态同步

## 4. 自动化步骤中的进样泵语义
### 步骤数据结构
```json
{
  "pump": {
    "enable": true,
    "speed": 60,
    "duration_ms": 3000
  }
}
```

### 执行流程
1. `_send_automation_step()` 先发送电机指令，等待 150ms 后发送进样泵 `PUMP:SET:<speed>` + `PUMP:ON`
2. `_wait_for_automation_step()` 等待 `duration_ms` 毫秒
3. 等待结束后自动发送 `PUMP:OFF` 关闭进样泵
4. 之后才开始计算步骤间隔（`interval` ms）

### 字段标准化
- 后端 `_normalize_sampling_sequence()` 补齐 `pump.enable`/`speed`/`duration_ms`（兼容旧配置）
- 前端 `normalizeStep()` 同步标准化

## 5. 当前边界
- 进样泵未接入 QGC FactGroup 遥测。
- 未定义独立 MAV_CMD 控制进样泵；当前推荐通过 Web 或自动化步骤驱动。
- 进样泵状态未映射到 `USV_STAT` 之外的独立 MAVLink 遥测名。

## 6. 后续可选扩展
- 新增 MAVLink 遥测名，如 `INJ_P_EN`、`INJ_P_SPD`。
- 将 `31014` 校准链路扩展到泵零点/系统校准统一流程。
- 若需要实船远程控制进样泵，可再设计独立 MAV_CMD 或 QGC 面板字段。
