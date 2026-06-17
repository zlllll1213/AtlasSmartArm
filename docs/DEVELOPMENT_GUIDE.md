# AtlasSmartArm 开发规范与接口契约

版本：v0.1  
日期：2026-06-17  
适用范围：Atlas 200I DK A2 智能机械臂电力运维与库房管理系统

## 1. 文档目标

本文件用于统一项目代码结构、模块边界、接口格式和联调流程，重点防止前后端接口调用出现字段不一致、单位不一致、状态不同步、硬件控制越权等问题。

本规范基于：

- `README.md` 中规划的硬件控制、AI 视觉、闭环抓取、可视化管理四大模块。
- `05机械臂使用手册.pdf`：机械臂样例、ROS2 服务、YOLOv5 OM 推理、相机校准、分拣与堆叠控制逻辑。
- `05开发板硬件使用手册.pdf`：Atlas 200I DK A2 启动、远程登录、默认 IP、Jupyter Lab、联网和硬件准备约束。

## 2. 总体架构

系统按职责拆成五层，跨层通信必须通过明确接口，不允许前端或业务代码绕过后端直接访问硬件。

```text
frontend/
  Web 可视化界面：库存、任务、识别结果、机械臂状态、视频/事件流

src/backend/
  业务 API：鉴权、任务编排、库存记录、接口协议、错误处理、日志

src/integration/
  闭环控制：目标识别结果 -> 坐标转换 -> 逆解 -> 抓取/堆叠任务

src/vision/
  视觉推理：摄像头采集、标定、YOLOv5/YOLOv8、OM 模型推理、结果后处理

src/hardware/
  机械臂适配：ROS2 Kinemarics 服务、串口舵机控制、设备状态和安全保护
```

### 2.1 调用方向

唯一允许的主调用链：

```text
Frontend -> Backend REST/WebSocket -> Integration -> Vision/Hardware -> Atlas/ROS2/Serial
```

禁止事项：

- 前端不得直接调用 ROS2、串口、Jupyter、SSH 或硬件脚本。
- 前端不得直接传递舵机底层指令，只能提交高层任务或经过校验的目标位姿。
- 后端不得把未声明单位的坐标、角度、时间字段透传给前端。
- 视觉模块不得直接修改库存，库存只能由后端任务状态机确认后写入。

## 3. 目录与文件规范

推荐目录结构如下，后续代码按此边界落位：

```text
.
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDE.md
│   ├── api/
│   │   └── openapi.yaml
│   └── hardware/
│       ├── calibration.md
│       └── deployment.md
├── src/
│   ├── backend/
│   ├── hardware/
│   ├── integration/
│   └── vision/
├── frontend/
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── scripts/
```

目录职责：

- `docs/api/openapi.yaml` 是前后端 HTTP API 的唯一事实来源。接口字段改动必须先改 OpenAPI，再改实现。
- `docs/hardware/` 记录真实设备部署、校准和故障处理步骤。
- `src/hardware/` 只能暴露稳定的硬件适配接口，不暴露串口实现细节给上层。
- `src/integration/` 负责任务编排、坐标转换、抓取流程和状态机。
- `tests/contract/` 放前后端契约测试，确保 Mock、OpenAPI 和后端响应一致。

## 4. 代码格式规范

### 4.1 通用规则

- 所有代码、接口字段、配置键名使用英文。
- 文件名使用小写字母、数字和下划线，示例：`arm_controller.py`、`task_state.ts`。
- 业务枚举使用稳定字符串，不使用中文作为接口值。
- 代码中需要保留关键注释，说明硬件约束、坐标转换、安全边界和非显而易见的算法逻辑。
- 禁止在代码中硬编码真实密码、设备 IP、模型路径和串口设备名，统一通过配置读取。

### 4.2 Python

推荐用于视觉、硬件适配和后端原型：

- Python 版本：`3.10+`。
- 格式化：`black`。
- 静态检查：`ruff`。
- 类型标注：公共函数必须写参数和返回值类型。
- 异常：硬件、视觉、任务异常必须转换为统一业务错误，不把底层异常堆栈直接返回给前端。

公共函数示例：

```python
def solve_inverse_kinematics(target: ArmPose) -> JointAngles:
    """将机械臂基坐标系目标位姿转换为关节角。

    这里保留注释是因为坐标单位和姿态角单位会直接影响真实机械臂动作安全。
    """
    return arm_adapter.solve_ik(target)
```

### 4.3 前端 TypeScript

- 前端必须启用 TypeScript 严格模式。
- API 类型从 OpenAPI 生成或手工维护在单一位置，不允许组件内临时拼字段。
- 请求层必须统一封装，不在页面组件中直接写 `fetch` 细节。
- 时间、状态、错误码必须走统一展示组件，避免各页面解释不一致。

### 4.4 Git 与提交

- 本仓库已经初始化 Git，后续每次修改代码或文档都必须提交。
- 每次提交只包含一个清晰主题。
- 提交信息建议格式：

```text
docs: add development guide
feat(backend): add task api contract
fix(hardware): clamp arm joint ranges
```

## 5. 硬件与运行环境约束

### 5.1 Atlas 200I DK A2

开发板基础约束：

- 推荐系统：Ubuntu 22.04 镜像。机械臂样例手册明确推荐 Ubuntu，未验证 openEuler 机械臂样例。
- Micro SD 卡推荐容量：不小于 `64GB`。
- 启动介质：SD 卡启动时拨码开关 2/3/4 为 `OFF/ON/OFF`。
- 上电后等待约 1 分钟再登录；首次启动可能自动升级固件，升级期间不要断电。
- 上电后不要插拔 SD 卡。

### 5.2 网络与登录

默认登录信息只用于实验环境，生产或展示环境必须改密。当前制卡工具中的网络接口配置如下：

| 网口 | IP 地址 | 子网掩码 | 默认网关 | 首选 DNS | 备用 DNS | 用途 |
| --- | --- | --- | --- | --- | --- | --- |
| `ETH1` | `192.168.137.100` | `255.255.255.0` | 留空 | `8.8.8.8` | `114.114.114.114` | 通过 RJ45 网线远程登录开发板 |
| `Type-C` | `192.168.0.2` | `255.255.255.0` | `192.168.0.1` | `8.8.8.8` | `114.114.114.114` | 通过 Type-C 数据线远程登录开发板 |

登录地址约定：

| 场景 | 默认地址 | 登录用户 | 默认密码 |
| --- | --- | --- | --- |
| Type-C 远程登录 | `192.168.0.2` | `root` | `Mind@123` |
| 以太网 eth1 远程登录 | `192.168.137.100` | `root` | `Mind@123` |
| Mac 远程登录 | 仅支持网线/Type-C 转 RJ45 | `root` | `Mind@123` |

规范：

- `.env` 只保存开发机自己的连接配置，不能提交真实密码。
- 后端配置项命名：

```text
ATLAS_NET_IFACE=ETH1
ATLAS_HOST=192.168.137.100
ATLAS_NETMASK=255.255.255.0
ATLAS_GATEWAY=
ATLAS_DNS_PRIMARY=8.8.8.8
ATLAS_DNS_SECONDARY=114.114.114.114
ATLAS_SSH_USER=root
ATLAS_SSH_PORT=22
ATLAS_API_BASE=http://192.168.137.100
```

### 5.3 Jupyter Lab 与样例运行

开发板镜像内置 Jupyter Lab，可用于调试样例和相机校准：

- 本机显示默认地址：`127.0.0.1:8888`。
- Type-C 远程登录默认地址：`192.168.0.2:8888`。
- 以太网 eth1 默认地址：`192.168.137.100:8888`。

Jupyter 只能作为调试入口，不作为正式系统接口。正式系统统一通过后端 API 暴露能力。

### 5.4 机械臂与摄像头

机械臂样例关键硬件：

- Atlas 200I DK A2 开发者套件。
- 机械臂及机械臂扩展板。
- USB 摄像头。
- 标定板地图。
- 40PIN 排线。
- 路由器和网线。

连接约束：

- 开发者套件 40PIN 接口连接机械臂扩展板 40PIN 接口。
- USB 摄像头连接开发者套件 USB 接口，并固定在机械臂上。
- 机械臂扩展板电源开关必须拨至 `ON`。
- 摄像头线较短，开发板与机械臂应靠近放置，避免运行时松脱。

## 6. 内部硬件接口规范

### 6.1 ROS2 运动学服务

机械臂手册中的核心内部服务为：

```text
dofbot_info/srv/Kinemarics.srv
```

请求字段：

| 字段 | 类型 | 单位 | 说明 |
| --- | --- | --- | --- |
| `tar_x` | `float64` | `m` | 机械臂基坐标系目标 X |
| `tar_y` | `float64` | `m` | 机械臂基坐标系目标 Y |
| `tar_z` | `float64` | `m` | 机械臂基坐标系目标 Z |
| `roll` | `float64` | `rad` | 目标姿态 Roll |
| `pitch` | `float64` | `rad` | 目标姿态 Pitch |
| `yaw` | `float64` | `rad` | 目标姿态 Yaw |
| `cur_joint1` - `cur_joint6` | `float64` | `deg` | 当前六个关节角 |
| `kin_name` | `string` | - | `fk` 或 `ik` |

响应字段：

| 字段 | 类型 | 单位 | 说明 |
| --- | --- | --- | --- |
| `joint1` - `joint6` | `float64` | `deg` | 逆运动学目标关节角 |
| `x` | `float64` | `m` | 正运动学到达 X |
| `y` | `float64` | `m` | 正运动学到达 Y |
| `z` | `float64` | `m` | 正运动学到达 Z |
| `roll` | `float64` | `rad` | 到达姿态 Roll |
| `pitch` | `float64` | `rad` | 到达姿态 Pitch |
| `yaw` | `float64` | `rad` | 到达姿态 Yaw |

调用规则：

- `kin_name=fk` 时只传当前关节角，后端返回基坐标系位姿。
- `kin_name=ik` 时传目标位姿，后端返回关节目标。
- 前端不得直接调用该 ROS2 服务。
- 后端硬件适配层必须做单位转换、范围限制和异常包装。

### 6.2 舵机控制边界

底层样例会调用类似以下动作：

```text
Arm_serial_servo_write(servo_id, angle, duration_ms)
Arm_serial_servo_write6_array([joint1, joint2, joint3, joint4, joint5, joint6], duration_ms)
```

规范：

- `servo_id` 只能由硬件适配层生成，前端和业务 API 不接受该字段。
- 公共 API 的关节角统一使用 `deg`。
- `duration_ms` 必须有上下限，默认范围建议 `100` 到 `3000`。
- 执行动作前必须检查机械臂状态为 `idle` 或当前任务持有控制锁。
- 任意时刻只能有一个运动任务持有机械臂控制锁。

### 6.3 配置文件

机械臂视觉与抓取样例依赖以下配置：

| 文件 | 说明 | 规范 |
| --- | --- | --- |
| `dp.bin` | 透视变换矩阵 | 相机校准后生成，视觉模块只读 |
| `XYT_config.txt` | 相机标定配置 | 标定流程更新，任务运行前必须存在 |
| `offset.txt` | 硬件误差补偿 | 抓取偏差修正时更新，并记录版本 |
| `coco_names.txt` | 模型标签 | 模型发布时同步更新 |
| `yolov5s_bs1.om` | Ascend OM 模型 | 放入模型目录，不提交大文件到 Git |

公共配置接口只暴露校准版本、更新时间和可调参数，不直接暴露二进制矩阵内容给前端。

## 7. 坐标、角度与单位规范

为避免前后端联调最常见的单位错误，所有接口字段必须带明确语义。

### 7.1 坐标系

| 坐标系 | 字段前缀 | 单位 | 原点 | 说明 |
| --- | --- | --- | --- | --- |
| 图像像素坐标 | `pixel_` | `px` | 图像左上角 | 摄像头原始/透视图坐标 |
| 归一化检测框 | `bbox_norm` | `0..1` | 图像左上角 | 模型检测输出 |
| 机械臂基坐标 | `arm_` | `m` | 机械臂基座 | 抓取和运动学目标 |
| 库房平面坐标 | `warehouse_` | `m` | 业务地图定义 | 库存可视化位置 |

### 7.2 图像尺寸

首版系统统一按手册样例使用：

```text
width=640
height=480
camera_index=0
```

若后续更换摄像头或分辨率，必须同时更新：

- `docs/api/openapi.yaml`
- 视觉配置
- 前端画布映射
- 契约测试样例

### 7.3 角度

| 场景 | 单位 | 说明 |
| --- | --- | --- |
| 前端展示关节角 | `deg` | 对用户友好 |
| 后端公共 API 关节角 | `deg` | 和样例舵机控制一致 |
| ROS2 姿态角 RPY | `rad` | 和机器人运动学约定一致 |
| 前端展示姿态角 | `deg` | 前端自行从后端返回值转换或由后端提供展示字段 |

字段命名必须体现单位：

```text
joint1_deg
duration_ms
confidence
timestamp_ms
arm_x_m
roll_rad
```

## 8. 公共 API 规范

### 8.1 基础约定

- API 前缀：`/api/v1`
- 数据格式：`application/json; charset=utf-8`
- 时间格式：ISO 8601 UTC 字符串，字段名为 `created_at`、`updated_at`。
- 请求追踪：所有响应必须包含 `request_id`。
- 分页参数：`page` 从 `1` 开始，`page_size` 默认 `20`，最大 `100`。
- 幂等写入：创建任务类接口支持 `Idempotency-Key` 请求头。

### 8.2 统一响应格式

成功响应：

```json
{
  "request_id": "req_20260617_000001",
  "success": true,
  "data": {},
  "error": null
}
```

失败响应：

```json
{
  "request_id": "req_20260617_000002",
  "success": false,
  "data": null,
  "error": {
    "code": "CALIBRATION_REQUIRED",
    "message": "Camera calibration is required before pick task.",
    "details": {
      "missing_files": ["dp.bin", "XYT_config.txt"]
    }
  }
}
```

### 8.3 错误码

| 错误码 | HTTP 状态 | 场景 |
| --- | --- | --- |
| `INVALID_ARGUMENT` | `400` | 字段缺失、类型错误、枚举非法 |
| `OUT_OF_RANGE` | `400` | 坐标、角度、时长超出安全范围 |
| `UNAUTHORIZED` | `401` | 未登录或 token 失效 |
| `FORBIDDEN` | `403` | 无权限执行硬件动作 |
| `NOT_FOUND` | `404` | 资源不存在 |
| `ARM_BUSY` | `409` | 机械臂正在执行其他任务 |
| `CALIBRATION_REQUIRED` | `409` | 缺少标定文件或标定过期 |
| `DEVICE_OFFLINE` | `503` | Atlas、摄像头或机械臂不可用 |
| `VISION_UNAVAILABLE` | `503` | 摄像头或模型推理不可用 |
| `KINEMATICS_FAILED` | `422` | 运动学求解失败 |
| `MODEL_NOT_LOADED` | `503` | OM 模型未加载 |
| `TASK_TIMEOUT` | `504` | 任务超时 |
| `INTERNAL` | `500` | 未归类服务端错误 |

## 9. API 清单

### 9.1 健康检查

```text
GET /api/v1/health
```

返回：

```json
{
  "request_id": "req_20260617_000003",
  "success": true,
  "data": {
    "service": "atlas-smart-arm-backend",
    "status": "ok",
    "version": "0.1.0",
    "time": "2026-06-17T10:00:00Z"
  },
  "error": null
}
```

### 9.2 系统状态

```text
GET /api/v1/system/status
```

返回字段：

```json
{
  "atlas": {
    "online": true,
    "host": "192.168.137.100",
    "network": {
      "iface": "ETH1",
      "ip_address": "192.168.137.100",
      "netmask": "255.255.255.0",
      "gateway": null,
      "dns": ["8.8.8.8", "114.114.114.114"]
    },
    "os": "ubuntu-22.04",
    "npu_available": true
  },
  "camera": {
    "online": true,
    "index": 0,
    "width": 640,
    "height": 480
  },
  "arm": {
    "online": true,
    "state": "idle",
    "control_lock": null
  },
  "vision": {
    "model_loaded": true,
    "model_name": "yolov5s_bs1.om"
  },
  "calibration": {
    "ready": true,
    "version": "calib_20260617_001"
  }
}
```

### 9.3 视觉检测

```text
POST /api/v1/vision/detect
```

请求：

```json
{
  "source": "camera",
  "camera_index": 0,
  "save_frame": false
}
```

响应 `data`：

```json
{
  "frame_id": "frame_20260617_000001",
  "image": {
    "width": 640,
    "height": 480
  },
  "detections": [
    {
      "object_id": "det_001",
      "label": "insulator",
      "category": "power_fitting",
      "confidence": 0.93,
      "bbox_norm": {
        "cx": 0.51,
        "cy": 0.47,
        "w": 0.12,
        "h": 0.10
      },
      "pixel_center": {
        "x_px": 326,
        "y_px": 226
      },
      "arm_position": {
        "x_m": 0.0015,
        "y_m": 0.2577,
        "z_m": 0.0
      }
    }
  ]
}
```

规范：

- `label` 必须来自模型标签文件或业务标签映射表。
- `category` 必须来自后端枚举，不直接使用模型原始分类作为库存类别。
- `confidence` 范围为 `0..1`。
- `arm_position` 只有在标定完成后才返回，否则返回 `null` 并提示 `CALIBRATION_REQUIRED`。

### 9.4 标定状态

```text
GET /api/v1/calibration/status
```

返回：

```json
{
  "ready": true,
  "version": "calib_20260617_001",
  "files": {
    "dp_bin": true,
    "xyt_config": true,
    "offset": true
  },
  "image": {
    "width": 640,
    "height": 480
  },
  "updated_at": "2026-06-17T10:00:00Z"
}
```

### 9.5 更新抓取偏移

```text
PUT /api/v1/calibration/offset
```

请求：

```json
{
  "x_offset_m": 0.008,
  "y_offset_m": 0.0,
  "reason": "Manual correction after grasping behind the target."
}
```

规范：

- 偏移参数必须记录审计日志。
- 修改后必须标记当前校准版本。
- 不允许前端直接上传或覆盖 `dp.bin`。

### 9.6 正运动学

```text
POST /api/v1/arm/kinematics/fk
```

请求：

```json
{
  "joints": {
    "joint1_deg": 90,
    "joint2_deg": 80,
    "joint3_deg": 50,
    "joint4_deg": 50,
    "joint5_deg": 265,
    "joint6_deg": 30
  }
}
```

响应 `data`：

```json
{
  "pose": {
    "x_m": 0.12,
    "y_m": 0.18,
    "z_m": 0.05,
    "roll_rad": 0.0,
    "pitch_rad": 1.57,
    "yaw_rad": 0.0
  }
}
```

### 9.7 逆运动学

```text
POST /api/v1/arm/kinematics/ik
```

请求：

```json
{
  "pose": {
    "x_m": 0.0015,
    "y_m": 0.2577,
    "z_m": 0.0,
    "roll_rad": 0.0,
    "pitch_rad": 1.57,
    "yaw_rad": 0.0
  }
}
```

响应 `data`：

```json
{
  "joints": {
    "joint1_deg": 91.2,
    "joint2_deg": 72.4,
    "joint3_deg": 18.5,
    "joint4_deg": 58.9,
    "joint5_deg": 265.0,
    "joint6_deg": 30.0
  },
  "reachable": true
}
```

### 9.8 安全移动

```text
POST /api/v1/arm/move
```

请求：

```json
{
  "target": {
    "type": "joints",
    "joints": {
      "joint1_deg": 90,
      "joint2_deg": 80,
      "joint3_deg": 50,
      "joint4_deg": 50,
      "joint5_deg": 265,
      "joint6_deg": 30
    }
  },
  "duration_ms": 1000,
  "dry_run": false
}
```

规范：

- 默认只允许管理员或设备控制服务调用。
- 普通前端页面应优先调用任务接口，而不是直接调用移动接口。
- `dry_run=true` 时只做运动学和范围校验，不向串口发指令。

### 9.9 急停

```text
POST /api/v1/arm/emergency-stop
```

规范：

- 此接口必须最高优先级执行。
- 调用后机械臂状态进入 `fault` 或 `stopped`。
- 恢复必须通过人工确认接口，不允许任务自动恢复。

### 9.10 分拣任务

```text
POST /api/v1/tasks/pick-sort
```

请求：

```json
{
  "target": {
    "mode": "auto_detect",
    "labels": ["insulator", "screwdriver", "relay"]
  },
  "destination": {
    "type": "category_bin",
    "category": "tool"
  },
  "options": {
    "dry_run": false,
    "max_retry": 1
  }
}
```

响应：

```json
{
  "task_id": "task_20260617_000001",
  "type": "pick_sort",
  "state": "queued"
}
```

### 9.11 堆叠任务

```text
POST /api/v1/tasks/stack
```

请求：

```json
{
  "target": {
    "mode": "auto_detect",
    "labels": ["component_box"]
  },
  "stack": {
    "slot_id": "stack_area_01",
    "max_layers": 4
  }
}
```

### 9.12 查询任务

```text
GET /api/v1/tasks/{task_id}
```

返回 `data`：

```json
{
  "task_id": "task_20260617_000001",
  "type": "pick_sort",
  "state": "moving",
  "progress": 0.55,
  "current_step": "moving_to_target",
  "created_at": "2026-06-17T10:00:00Z",
  "updated_at": "2026-06-17T10:00:08Z",
  "result": null
}
```

任务状态枚举：

```text
queued
detecting
planning
moving
verifying
succeeded
failed
cancelled
paused
```

### 9.13 取消任务

```text
POST /api/v1/tasks/{task_id}/cancel
```

规范：

- 仅允许取消 `queued`、`detecting`、`planning` 状态任务。
- `moving` 状态需要先进入安全暂停点，不能直接中断串口动作。
- 急停场景使用 `/api/v1/arm/emergency-stop`。

## 10. WebSocket 事件规范

实时状态统一走 WebSocket：

```text
WS /ws/v1/events
```

事件包格式：

```json
{
  "event_id": "evt_20260617_000001",
  "type": "arm.state.changed",
  "time": "2026-06-17T10:00:00Z",
  "data": {}
}
```

事件类型：

| 类型 | 说明 |
| --- | --- |
| `system.status.changed` | Atlas、摄像头、模型、机械臂状态变化 |
| `vision.detection.created` | 新识别结果 |
| `task.state.changed` | 任务状态变化 |
| `task.progress.updated` | 任务进度变化 |
| `arm.state.changed` | 机械臂状态变化 |
| `arm.fault.raised` | 硬件故障 |
| `inventory.item.updated` | 库存变化 |

前端规范：

- 前端以 REST 查询为准，WebSocket 只用于实时刷新。
- WebSocket 断开后必须自动重连，并重新拉取 `/api/v1/system/status` 与当前任务。
- 前端不能仅凭 WebSocket 事件认定任务最终成功，必须查询任务详情确认。

## 11. 库存与业务对象规范

### 11.1 物资对象

```json
{
  "item_id": "item_001",
  "name": "绝缘子",
  "category": "power_fitting",
  "label": "insulator",
  "quantity": 12,
  "location": {
    "area": "A",
    "shelf": "A-01",
    "slot": "A-01-03"
  },
  "updated_at": "2026-06-17T10:00:00Z"
}
```

枚举建议：

```text
electronic_component
power_fitting
tool
consumable
unknown
```

### 11.2 库存接口

首版接口：

```text
GET  /api/v1/inventory/items
POST /api/v1/inventory/items
GET  /api/v1/inventory/items/{item_id}
PUT  /api/v1/inventory/items/{item_id}
POST /api/v1/inventory/inbound
POST /api/v1/inventory/outbound
POST /api/v1/inventory/audit
```

规范：

- 机械臂任务成功后，由后端写入入库、出库或盘点记录。
- 前端人工调整库存必须留下 `operator` 和 `reason`。
- 视觉识别结果只能作为候选，不自动覆盖库存主数据。

## 12. 安全状态机

机械臂状态：

```text
offline
initializing
idle
detecting
planning
moving
paused
stopped
fault
```

状态规则：

- 只有 `idle` 可以开始新任务。
- `moving` 状态不允许启动第二个任务。
- `fault` 状态必须人工复位。
- `stopped` 状态必须重新执行设备健康检查后才能回到 `idle`。
- 任意任务开始前必须检查 `calibration.ready=true`。

任务执行标准流程：

```text
1. 检查系统状态
2. 检查校准状态
3. 获取图像
4. 执行模型推理
5. 目标过滤与业务类别映射
6. 图像坐标转换为机械臂基坐标
7. 逆运动学求解
8. dry-run 安全校验
9. 申请机械臂控制锁
10. 执行抓取/分拣/堆叠动作
11. 释放控制锁
12. 写入任务结果和库存记录
```

## 13. 前后端联调流程

### 13.1 接口变更流程

1. 修改 `docs/api/openapi.yaml`。
2. 更新接口变更说明。
3. 后端实现接口或更新 Mock。
4. 前端更新类型和调用。
5. 运行契约测试。
6. Git commit。

### 13.2 联调前检查

- OpenAPI 中字段名、类型、必填项、枚举、单位已写清楚。
- 前端请求示例和后端响应示例一致。
- 所有任务接口都有错误响应样例。
- 后端在无硬件环境下可启用 Mock 模式。
- 硬件联调前完成相机标定，并确认 `dp.bin`、`XYT_config.txt`、`offset.txt` 存在。

### 13.3 Mock 规范

后端应支持：

```text
ATLAS_MOCK=true
VISION_MOCK=true
ARM_MOCK=true
```

Mock 模式必须模拟：

- 正常识别结果。
- 空识别结果。
- 机械臂忙碌。
- 标定缺失。
- 运动学不可达。
- 任务超时。

## 14. 测试规范

### 14.1 单元测试

必须覆盖：

- 坐标转换。
- 角度和范围校验。
- 错误码映射。
- 任务状态机。
- 模型标签到业务类别映射。

### 14.2 契约测试

必须覆盖：

- OpenAPI 示例能被后端实际返回匹配。
- 前端生成类型与后端响应字段一致。
- 统一错误响应格式一致。
- WebSocket 事件格式一致。

### 14.3 硬件联调测试

硬件联调最小清单：

- Atlas 可 SSH 登录。
- 摄像头 `camera_index=0` 可读取 `640x480` 图像。
- OM 模型加载成功。
- 相机校准完成。
- `fk` 和 `ik` 均可调用。
- `dry_run` 能发现不可达目标。
- 急停接口可用。
- 单次分拣任务成功。
- 单次堆叠任务成功。

## 15. 日志与审计

后端日志至少包含：

```text
request_id
task_id
operator
api_path
latency_ms
arm_state
calibration_version
model_name
error_code
```

硬件动作审计必须记录：

- 操作人或服务名。
- 任务 ID。
- 起止时间。
- 目标位姿或目标关节角。
- 是否 `dry_run`。
- 执行结果。
- 错误原因。

禁止在日志中记录：

- 登录密码。
- SSH 私钥。
- Jupyter token。
- 未脱敏的个人信息。

## 16. 配置规范

推荐环境变量：

```text
APP_ENV=development
APP_PORT=8080

ATLAS_NET_IFACE=ETH1
ATLAS_HOST=192.168.137.100
ATLAS_NETMASK=255.255.255.0
ATLAS_GATEWAY=
ATLAS_DNS_PRIMARY=8.8.8.8
ATLAS_DNS_SECONDARY=114.114.114.114
ATLAS_SSH_USER=root
ATLAS_SSH_PORT=22

CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480

VISION_MODEL_PATH=/opt/atlas-smart-arm/models/yolov5s_bs1.om
VISION_LABELS_PATH=/opt/atlas-smart-arm/models/coco_names.txt

CALIBRATION_DIR=/opt/atlas-smart-arm/calibration

ATLAS_MOCK=false
VISION_MOCK=false
ARM_MOCK=false
```

规范：

- `.env.example` 可提交，`.env` 不提交。
- 路径类配置必须支持开发机和 Atlas 设备分别配置。
- 前端只通过后端 API 获取运行状态，不读取后端 `.env`。

## 17. 发布与部署约定

首版部署路径建议：

```text
/opt/atlas-smart-arm/
  backend/
  models/
  calibration/
  logs/
```

模型发布规则：

- OM 模型和标签文件必须成对发布。
- 模型版本写入后端状态接口。
- 模型变更需要回归视觉检测、坐标转换和抓取任务。

校准发布规则：

- 相机校准文件与硬件位置绑定。
- 移动摄像头、机械臂、标定板后必须重新标定。
- `offset.txt` 修改后必须保留修改原因。

## 18. 关键开发原则

- API 先行：先定 OpenAPI，再写前后端代码。
- 单位显式：所有坐标、角度、时间字段必须在字段名或 schema 中声明单位。
- 状态集中：任务状态只能由后端状态机推进。
- 硬件隔离：前端不接触 ROS2、串口、SSH、Jupyter。
- 可模拟：无硬件环境也能跑前端、后端和契约测试。
- 可追踪：任务、接口、硬件动作都必须有 `request_id` 或 `task_id`。
- 先 dry-run：真实移动前必须支持校验路径。
- 失败可解释：每个失败都返回稳定错误码和可读 `message`。

## 19. 首版落地清单

建议按以下顺序推进：

1. 创建 `docs/api/openapi.yaml`，写入本文件定义的首版接口。
2. 创建后端统一响应结构和错误码枚举。
3. 创建 `ArmAdapter`、`VisionService`、`TaskService` 三个后端边界接口。
4. 实现 Mock 模式，前端先基于 Mock 联调。
5. 接入 Atlas SSH/ROS2/串口前，完成硬件部署文档。
6. 接入 `Kinemarics.srv` 正逆运动学调用。
7. 接入相机读取、标定文件检查和 OM 模型推理。
8. 实现分拣和堆叠任务状态机。
9. 接入库存入库、出库和盘点记录。
10. 补齐契约测试和硬件联调测试清单。

## 20. 文档维护规则

- 接口字段变化必须同步更新本文件和 OpenAPI。
- 硬件连接、默认 IP、启动命令变化必须同步更新 `docs/hardware/deployment.md`。
- 标定流程变化必须同步更新 `docs/hardware/calibration.md`。
- 每次文档更新必须单独提交 Git commit。
