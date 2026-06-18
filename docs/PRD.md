# 智能机械臂电力智能运维/库房管理系统 — 需求与开发文档

版本：v1.0
日期：2026-06-18
项目：实践题目8 — 基于华为Atlas 200I DK智能机械臂的电力智能运维/电力库房管理

---

## 1. 项目概述

### 1.1 项目背景

本项目基于华为 Atlas 200I DK A2 开发者套件与六自由度智能机械臂，面向电力行业场景，实现电子元器件、电力金具、工具等物资的自动识别、精准抓取、分类堆叠与移动，并构建一套可视化电力智能运维与库房管理系统。

### 1.2 实践内容映射

| 编号 | 实践内容 | 对应模块 |
|------|----------|----------|
| (1) | 智能机械臂的安装部署 | 硬件部署模块 |
| (2) | 目标识别算法 | AI 视觉模块 |
| (3) | 机械臂控制 | 硬件控制模块 |
| (4) | 色块识别、抓取与堆叠 | 集成控制模块 |
| (5) | 电子元器件/电力金具/工具识别与抓取 | AI 视觉 + 集成控制模块 |
| (6) | 可视化电力智能运维/库房管理系统 | 可视化管理模块 |

### 1.3 技术栈

| 层级 | 技术选型 |
|------|----------|
| 边缘计算 | Huawei Atlas 200I DK A2 (Ascend 310) |
| AI 推理 | YOLOv5/YOLOv8 → OM 模型 (CANN) |
| 机械臂控制 | Python, ROS2 Kinemarics 服务, 串口通信 |
| 后端 | Python 3.10+ (FastAPI) |
| 前端 | TypeScript (React/Vue3) |
| 视觉处理 | OpenCV, 相机标定, 透视变换 |
| 实时通信 | WebSocket + REST API |
| 操作系统 | Ubuntu 22.04 (Atlas 端) |

---

## 2. 系统架构

### 2.1 五层架构

```
frontend/          Web 可视化界面（库存、任务、识别结果、机械臂状态、视频流）
    ↓ REST/WebSocket
src/backend/       业务 API（鉴权、任务编排、库存记录、接口协议、错误处理、日志）
    ↓
src/integration/   闭环控制（识别→坐标转换→逆解→抓取/堆叠任务状态机）
    ↓
src/vision/        视觉推理（摄像头采集、标定、YOLO推理、后处理）
src/hardware/      机械臂适配（ROS2 运动学服务、串口舵机、设备状态）
```

### 2.2 核心调用链

```
Frontend → Backend REST/WebSocket → Integration → Vision / Hardware → Atlas / ROS2 / Serial
```

### 2.3 硬性约束

- 前端不得直接调用 ROS2、串口、SSH 或硬件脚本
- 前端不得直接传递舵机底层指令，只能提交高层任务
- 视觉模块不得直接修改库存，库存由后端任务状态机确认后写入
- 所有坐标、角度、时间字段必须在字段名中声明单位

---

## 3. 模块划分与分工

### 3.1 模块职责

| 模块 | 目录 | 职责 | 建议人数 |
|------|------|------|----------|
| 硬件适配 | `src/hardware/` | ROS2 运动学服务封装、串口舵机控制、设备状态监控、安全保护 | 1-2人 |
| AI 视觉 | `src/vision/` | 摄像头采集与标定、YOLO OM 模型推理、坐标转换、结果后处理 | 1-2人 |
| 闭环集成 | `src/integration/` | 任务状态机、抓取/分拣/堆叠流程编排、坐标转换、控制锁管理 | 1人 |
| 后端 API | `src/backend/` | REST/WebSocket API、鉴权、库存管理、日志审计、配置管理 | 1-2人 |
| 前端可视化 | `frontend/` | 库存面板、任务面板、实时监控、机械臂状态、视频流展示 | 1-2人 |

### 3.2 推荐团队配置

**3人团队：**
- A (硬件+集成): `src/hardware/` + `src/integration/`
- B (视觉+后端): `src/vision/` + `src/backend/`
- C (前端): `frontend/`

**4人团队：**
- A: `src/hardware/` + 硬件部署
- B: `src/vision/` + 模型训练
- C: `src/backend/` + `src/integration/`
- D: `frontend/`

**5人团队：**
- A: `src/hardware/`
- B: `src/vision/`
- C: `src/integration/`
- D: `src/backend/`
- E: `frontend/`

### 3.3 模块间接口契约

所有接口以 `docs/api/openapi.yaml` 为唯一事实来源。接口变更流程：

```
修改 OpenAPI → 更新接口说明 → 后端实现/Mock → 前端更新类型 → 契约测试 → Git commit
```

---

## 4. 开发分期

### 第一期：基础设施搭建（第1-2周）

**目标**：硬件环境就绪，开发环境可运行，基础通信链路调通

| 任务 | 负责人 | 产出物 |
|------|--------|--------|
| Atlas 200I DK A2 系统烧录与启动 | A | 可 SSH 登录的开发板 |
| 网络配置（ETH1/Type-C） | A | `192.168.137.100:22` 可访问 |
| 机械臂组装与扩展板连接 | A | 40PIN 排线连接，电源开关 ON |
| USB 摄像头安装与固定 | B | 摄像头可读取 640×480 图像 |
| Jupyter Lab 环境验证 | A/B | `192.168.137.100:8888` 可访问 |
| 开发机 Python 环境搭建 | 全员 | `requirements.txt` |
| 前端项目脚手架 | C/D/E | `npm run dev` 可启动 |
| 项目目录结构初始化 | 全员 | 按 `DEVELOPMENT_GUIDE.md` 落位 |
| OpenAPI 规范文件创建 | D | `docs/api/openapi.yaml` |
| ssh 免密登录 & 文件同步脚本 | A | `scripts/sync.sh` |

**里程碑 M1**：Atlas 可远程登录，摄像头出图，机械臂可通电，前端项目可启动。

### 第二期：基础控制与视觉（第2-3周）

**目标**：机械臂可控制运动，摄像头可采集图像，色块识别可用

| 任务 | 负责人 | 产出物 |
|------|--------|--------|
| ROS2 Kinemarics 服务封装 (`fk`/`ik`) | A | FK/IK 可调用并返回正确结果 |
| 串口舵机控制适配 (`Arm_serial_servo_write6_array`) | A | 6 关节联合运动 |
| 控制锁与安全边界校验 | A | 关节角范围限制、duration_ms 限制 |
| 急停接口实现 | A | `POST /api/v1/arm/emergency-stop` |
| 摄像头采集与参数配置 | B | 640×480, 30fps 采集 |
| 相机标定（对标定板） | B | `dp.bin`, `XYT_config.txt`, `offset.txt` |
| HSV 色块识别算法 | B | 红/蓝/绿/黄四色检测 |
| 图像坐标→机械臂基坐标转换 | B/C | 透视变换矩阵应用 |
| 后端 Mock 模式 | D | `ATLAS_MOCK/VISION_MOCK/ARM_MOCK` |
| 后端基础框架（FastAPI + 统一响应格式） | D | `request_id`, `success`, `data`, `error` |

**里程碑 M2**：Mock 模式下 `/api/v1/health` 可访问，机械臂可手动控制移动，色块识别可输出坐标。

### 第三期：色块抓取闭环（第3-4周）

**目标**：实现色块识别→坐标转换→抓取→堆叠的完整闭环

| 任务 | 负责人 | 产出物 |
|------|--------|--------|
| 分拣任务状态机 | C | `queued→detecting→planning→moving→succeeded/failed` |
| 抓取流程编排（识别→IK→移动→抓取→放置） | C | 单个目标完整抓取流程 |
| 堆叠任务实现 | C | 多层堆叠逻辑（max_layers 可配置） |
| 色块分拣任务 API | C/D | `POST /api/v1/tasks/pick-sort` |
| 堆叠任务 API | C/D | `POST /api/v1/tasks/stack` |
| 任务状态查询 API | D | `GET /api/v1/tasks/{task_id}` |
| 任务取消 API | D | `POST /api/v1/tasks/{task_id}/cancel` |
| 前端任务面板 | E | 任务创建、进度展示、状态轮询 |
| 色块识别结果可视化 | E | 图像标注框叠加显示 |
| WebSocket 事件推送 | D | `WS /ws/v1/events` |
| dry-run 安全校验 | C | 实际运动前运动学和范围校验 |

**里程碑 M3**：色块可被自动识别、抓取并堆叠到指定区域。前端可实时查看任务进度。

### 第四期：电力物资识别与抓取（第4-5周）

**目标**：实现对电子元器件、电力金具、工具的深度学习识别与精确抓取

| 任务 | 负责人 | 产出物 |
|------|--------|--------|
| 电力物资数据集采集与标注 | B | ≥3 类物资，每类 ≥200 张 |
| YOLOv5s 模型训练 | B | mAP ≥ 0.85 |
| ONNX → OM 模型转换 (ATC) | B | `yolov5s_bs1.om` |
| OM 模型加载与推理 (Ascend 310) | B | 推理延迟 < 100ms |
| 标签文件管理与业务类别映射 | B | `coco_names.txt`, 类别枚举 |
| 后处理与 NMS | B | 检测框过滤与去重 |
| 识别结果 API | B/D | `POST /api/v1/vision/detect` |
| 电力物资抓取参数调优 | C | 偏移补偿、抓取力度 |
| 多目标连续分拣 | C | 视野内多目标依次抓取 |
| 相机重新标定（含抓取偏移） | B | `offset.txt` 校准 |
| 前端检测结果可视化 | E | 检测类别、置信度、坐标叠加 |

**里程碑 M4**：可识别并抓取至少 3 类电力物资（如绝缘子、螺丝刀、继电器）。

### 第五期：可视化管理与运维系统（第5-6周）

**目标**：完成电力库房管理系统和智能运维监控面板

| 任务 | 负责人 | 产出物 |
|------|--------|--------|
| 库存 CRUD API | D | `GET/POST/PUT /api/v1/inventory/items` |
| 入库/出库/盘点 API | D | `POST /api/v1/inventory/inbound|outbound|audit` |
| 库存与任务联动（抓取后自动登记） | C/D | 任务成功→库存自动写入 |
| 系统状态 API | D | `GET /api/v1/system/status` |
| 标定状态 API | D | `GET /api/v1/calibration/status` |
| 偏移更新 API | D | `PUT /api/v1/calibration/offset` |
| 前端库存管理面板 | E | 物资列表、入库/出库、盘点 |
| 前端系统监控面板 | E | Atlas、摄像头、机械臂状态卡片 |
| 前端实时视频流 | E | MJPEG/WebRTC 流展示 |
| 前端事件日志面板 | E | WebSocket 事件列表 |
| 前端仪表盘首页 | E | 关键指标汇总 |
| 日志与审计系统 | D | request_id, task_id, 硬件动作审计 |

**里程碑 M5**：可视化管理系统可展示库存、监控设备状态、查看实时视频和任务日志。

### 第六期：集成、测试与优化（第6-7周）

**目标**：系统联调、测试覆盖、性能优化与文档完善

| 任务 | 负责人 | 产出物 |
|------|--------|--------|
| 契约测试 (OpenAPI ↔ 后端) | D/E | `tests/contract/` |
| 坐标转换单元测试 | B/C | `tests/unit/test_coordinate.py` |
| 任务状态机集成测试 | C | `tests/integration/test_task_fsm.py` |
| 硬件联调测试清单 | A/C | 9 项最小测试清单 |
| Mock 模式全覆盖 | D | 正常/空检测/忙碌/无标定/超时 |
| 错误码全覆盖 | D | 13 个错误码 |每一场景 |
| 性能测试 | B | 推理延迟、任务端到端延迟 |
| 前端异常状态处理 | E | 设备离线、任务失败、超时 |
| 部署文档 | A | `docs/hardware/deployment.md` |
| 校准文档 | B | `docs/hardware/calibration.md` |
| 项目总结与答辩材料 | 全员 | PPT、演示视频 |

**里程碑 M6**：全系统可演示，所有测试通过，文档完备。

---

## 5. 统一接口规范

本项目接口规范已在 `docs/DEVELOPMENT_GUIDE.md` 中详细定义，以下为关键约定摘要。完整接口定义参见 `docs/api/openapi.yaml`。

### 5.1 基础约定

| 项目 | 规范 |
|------|------|
| API 前缀 | `/api/v1` |
| 数据格式 | `application/json; charset=utf-8` |
| 时间格式 | ISO 8601 UTC |
| 请求追踪 | 所有响应含 `request_id` |
| 分页 | `page` 从 1 开始, `page_size` 默认 20, 最大 100 |
| 幂等写入 | 创建类接口支持 `Idempotency-Key` 头 |

### 5.2 统一响应格式

```json
{
  "request_id": "req_20260618_000001",
  "success": true,
  "data": {},
  "error": null
}
```

### 5.3 单位约定

| 场景 | 单位 | 字段名约定 |
|------|------|------------|
| 机械臂基坐标系位置 | `m` | `arm_x_m`, `arm_y_m`, `arm_z_m` |
| 图像像素坐标 | `px` | `pixel_x_px`, `pixel_y_px` |
| 归一化检测框 | `0..1` | `bbox_norm.{cx,cy,w,h}` |
| 前端展示关节角 | `deg` | `joint1_deg` ~ `joint6_deg` |
| ROS2 姿态角 RPY | `rad` | `roll_rad`, `pitch_rad`, `yaw_rad` |
| 持续时间 | `ms` | `duration_ms` |
| 置信度 | `0..1` | `confidence` |

### 5.4 API 清单

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/health` | 健康检查 |
| `GET` | `/api/v1/system/status` | 系统状态（Atlas、摄像头、机械臂、视觉、标定） |
| `POST` | `/api/v1/vision/detect` | 触发目标检测 |
| `GET` | `/api/v1/calibration/status` | 查询标定状态 |
| `PUT` | `/api/v1/calibration/offset` | 更新抓取偏移量 |
| `POST` | `/api/v1/arm/kinematics/fk` | 正运动学（关节角→位姿） |
| `POST` | `/api/v1/arm/kinematics/ik` | 逆运动学（位姿→关节角） |
| `POST` | `/api/v1/arm/move` | 安全移动（支持 dry_run） |
| `POST` | `/api/v1/arm/emergency-stop` | 急停 |
| `POST` | `/api/v1/tasks/pick-sort` | 创建分拣任务 |
| `POST` | `/api/v1/tasks/stack` | 创建堆叠任务 |
| `GET` | `/api/v1/tasks/{task_id}` | 查询任务详情 |
| `POST` | `/api/v1/tasks/{task_id}/cancel` | 取消任务 |
| `GET` | `/api/v1/inventory/items` | 库存列表 |
| `POST` | `/api/v1/inventory/items` | 新增物资 |
| `GET` | `/api/v1/inventory/items/{item_id}` | 物资详情 |
| `PUT` | `/api/v1/inventory/items/{item_id}` | 更新物资 |
| `POST` | `/api/v1/inventory/inbound` | 入库 |
| `POST` | `/api/v1/inventory/outbound` | 出库 |
| `POST` | `/api/v1/inventory/audit` | 盘点 |

### 5.5 错误码

| 错误码 | HTTP | 场景 |
|--------|------|------|
| `INVALID_ARGUMENT` | 400 | 字段缺失/类型错误 |
| `OUT_OF_RANGE` | 400 | 坐标/角度超出安全范围 |
| `ARM_BUSY` | 409 | 机械臂正在执行其他任务 |
| `CALIBRATION_REQUIRED` | 409 | 标定缺失或过期 |
| `DEVICE_OFFLINE` | 503 | 设备不可用 |
| `VISION_UNAVAILABLE` | 503 | 摄像头/模型不可用 |
| `KINEMATICS_FAILED` | 422 | 运动学求解失败 |
| `MODEL_NOT_LOADED` | 503 | OM 模型未加载 |
| `TASK_TIMEOUT` | 504 | 任务超时 |
| `INTERNAL` | 500 | 未归类内部错误 |

### 5.6 任务状态机

```text
queued → detecting → planning → moving → verifying → succeeded
                       ↓           ↓          ↓
                     paused      failed    cancelled
```

### 5.7 机械臂状态机

```text
offline → initializing → idle ↔ detecting ↔ planning ↔ moving
                              ↘ paused
                              ↘ stopped (需健康检查恢复)
                              ↘ fault (需人工复位)
```

### 5.8 物资类别枚举

```text
electronic_component  (电子元器件)
power_fitting         (电力金具)
tool                  (工具)
consumable            (耗材)
unknown              (未知)
```

---

## 6. 硬件部署规范

### 6.1 Atlas 200I DK A2 配置

| 项目 | 参数 |
|------|------|
| 系统 | Ubuntu 22.04 |
| SD 卡 | ≥ 64GB |
| 拨码开关 (SD 启动) | 2=OFF, 3=ON, 4=OFF |
| ETH1 IP | `192.168.137.100 / 255.255.255.0` |
| Type-C IP | `192.168.0.2 / 255.255.255.0` |
| SSH 用户 | `root` |
| Jupyter Lab | `192.168.137.100:8888` (ETH1) |

### 6.2 硬件连接

```
Atlas 200I DK A2 (40PIN) ──排线── 机械臂扩展板 (40PIN)
USB 摄像头 ─────────────── USB ── Atlas 开发板
电源适配器 ─────────────── DC ── Atlas 开发板
路由器 ───────────────── RJ45 ── Atlas ETH1
机械臂扩展板电源开关: ON
```

### 6.3 关键配置文件

| 文件 | 说明 | 生成方式 |
|------|------|----------|
| `dp.bin` | 透视变换矩阵 | 相机标定生成 |
| `XYT_config.txt` | 相机标定配置 | 标定流程生成 |
| `offset.txt` | 抓取偏移补偿 | 抓取偏差修正 |
| `coco_names.txt` | 模型标签文件 | 模型训练生成 |
| `yolov5s_bs1.om` | Ascend OM 模型 | ATC 工具转换 |

---

## 7. 目标识别算法规范

### 7.1 色块识别（第三期）

- 方法：HSV 颜色空间分割 + 轮廓检测
- 支持颜色：红、蓝、绿、黄
- 输出：色块中心像素坐标 + 包围框
- 后处理：透视变换后转换到机械臂基坐标系

### 7.2 电力物资识别（第四期）

- 模型：YOLOv5s
- 部署：ONNX → OM (Ascend 310 推理)
- 输入：640×480 RGB
- 输出：检测框 (label, confidence, bbox_norm, pixel_center)
- 类别映射：模型标签 → 业务类别枚举
- 训练数据：≥3 类 (电子元器件/电力金具/工具)，每类 ≥200 张
- 目标 mAP：≥ 0.85

### 7.3 识别结果数据结构

```json
{
  "object_id": "det_001",
  "label": "insulator",
  "category": "power_fitting",
  "confidence": 0.93,
  "bbox_norm": { "cx": 0.51, "cy": 0.47, "w": 0.12, "h": 0.10 },
  "pixel_center": { "x_px": 326, "y_px": 226 },
  "arm_position": { "x_m": 0.0015, "y_m": 0.2577, "z_m": 0.0 }
}
```

---

## 8. 机械臂控制规范

### 8.1 任务执行标准流程

```
1. 检查系统状态 (GET /api/v1/system/status)
2. 检查标定状态 (GET /api/v1/calibration/status)
3. 获取图像 → 模型推理
4. 目标过滤与业务类别映射
5. 图像坐标 → 机械臂基坐标 (透视变换)
6. 逆运动学求解 (POST /api/v1/arm/kinematics/ik)
7. dry-run 安全校验
8. 申请机械臂控制锁
9. 执行抓取/分拣/堆叠动作
10. 释放控制锁
11. 写入任务结果和库存记录
```

### 8.2 安全约束

- 任意时刻只能有一个运动任务持有控制锁
- `duration_ms` 范围：100~3000
- 执行动作前必须确认机械臂状态为 `idle`
- 坐标/角度必须在安全范围内
- 支持 dry_run 模式进行预校验
- 急停接口最高优先级执行

---

## 9. 目录结构

```
.
├── README.md
├── docs/
│   ├── PRD.md                     # 本文件
│   ├── DEVELOPMENT_GUIDE.md       # 开发规范与接口契约（权威参考）
│   ├── api/
│   │   └── openapi.yaml           # API 唯一事实来源
│   └── hardware/
│       ├── calibration.md         # 标定流程
│       └── deployment.md          # 部署文档
├── src/
│   ├── backend/                   # 业务 API
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   └── middleware/
│   ├── hardware/                  # 机械臂适配
│   │   ├── arm_adapter.py
│   │   ├── kinematics.py
│   │   └── serial_controller.py
│   ├── integration/               # 闭环控制
│   │   ├── task_fsm.py
│   │   ├── pick_place.py
│   │   └── coordinate_transform.py
│   └── vision/                    # 视觉推理
│       ├── camera.py
│       ├── detector.py
│       ├── calibration.py
│       └── preprocessing.py
├── frontend/                      # Web 可视化
│   ├── src/
│   │   ├── api/                   # API 类型与调用
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   └── ...
├── tests/
│   ├── contract/                  # 契约测试
│   ├── integration/               # 集成测试
│   └── unit/                      # 单元测试
└── scripts/                       # 部署与同步脚本
```

---

## 10. 验收标准

### 10.1 功能验收

| 序号 | 验收项 | 标准 |
|------|--------|------|
| 1 | 开发板远程登录 | SSH 免密登录，ping 延迟 < 5ms |
| 2 | 摄像头采集 | 640×480, ≥15fps, 画面清晰 |
| 3 | 相机标定 | dp.bin 生成，透视变换误差 < 5px |
| 4 | 色块识别 | 四色均可识别，准确率 ≥ 95% |
| 5 | 机械臂运动 | 6 关节联动，定位误差 < 5mm |
| 6 | FK/IK | 正逆解可相互验证，角度误差 < 2° |
| 7 | 色块抓取 | 单色块抓取成功率 ≥ 80% |
| 8 | 色块堆叠 | 3 层堆叠不倒 |
| 9 | 电力物资检测 | 3 类物资 mAP ≥ 0.85 |
| 10 | OM 推理 | 单帧推理延迟 < 100ms |
| 11 | 电力物资抓取 | 抓取成功率 ≥ 70% |
| 12 | 库存管理 | CRUD + 入出库 + 盘点全部可用 |
| 13 | 实时监控 | WebSocket 事件推送延迟 < 500ms |
| 14 | 急停 | 触发后 100ms 内停止机械臂运动 |
| 15 | Mock 模式 | 无硬件环境前后端可完整联调 |

### 10.2 代码质量

- 所有公共函数有类型标注
- 契约测试覆盖所有 API 端点
- 单元测试覆盖坐标转换、状态机、错误码
- OpenAPI 与后端响应一致
- 前端 TypeScript 严格模式无错误

---

## 11. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| Atlas 开发板到货延迟 | 所有硬件相关任务延期 | 优先利用 Mock 模式开发后端与前端 |
| 机械臂故障 | 抓取任务无法执行 | 提前验收硬件，预备备用舵机 |
| 模型训练数据不足 | 识别准确率低 | 数据增强、迁移学习、合成数据 |
| OM 模型转换失败 | 无法在 NPU 推理 | 保留 ONNX CPU 推理回退方案 |
| 相机标定精度不足 | 抓取偏移过大 | 多次标定取平均，offset.txt 补偿 |
| 机械臂运动不可达 | 任务失败 | 增加可到达区域预校验，优化物品摆放 |
| 网络延迟高 | WebSocket 中断 | 前端自动重连，REST 查询兜底 |

---

## 12. 文档参考

| 文档 | 用途 |
|------|------|
| `docs/DEVELOPMENT_GUIDE.md` | 开发规范与接口契约（权威参考，所有接口定义以此为唯一事实来源） |
| `docs/PRD.md` (本文件) | 项目需求、分期计划、分工方案 |
| `docs/api/openapi.yaml` | REST/WebSocket API 正式定义 |
| `docs/hardware/deployment.md` | 硬件部署步骤 |
| `docs/hardware/calibration.md` | 相机标定流程 |
| `docs/05开发板硬件使用手册.pdf` | Atlas 200I DK A2 硬件参考 |
| `docs/05机械臂使用手册.pdf` | 机械臂 ROS2 样例、舵机控制参考 |
| `docs/课程安排20260615.pdf` | 课程时间规划 |

---

## 附录 A：接口字段单位速查表

| 字段模式 | 单位 | 示例值 |
|----------|------|--------|
| `*_m` | 米 | `0.2577` |
| `*_mm` | 毫米 | `25.0` |
| `*_deg` | 度 | `90.0` |
| `*_rad` | 弧度 | `1.5708` |
| `*_px` | 像素 | `326` |
| `*_ms` | 毫秒 | `1000` |
| `confidence` | 0..1 | `0.93` |
| `timestamp_ms` | Unix 毫秒 | `1718700000000` |
| `progress` | 0..1 | `0.55` |
| `*_norm` | 0..1 归一化 | `0.51` |

## 附录 B：环境变量速查表

```bash
APP_ENV=development
APP_PORT=8080
ATLAS_HOST=192.168.137.100
ATLAS_SSH_USER=root
ATLAS_SSH_PORT=22
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
VISION_MODEL_PATH=/opt/atlas-smart-arm/models/yolov5s_bs1.om
CALIBRATION_DIR=/opt/atlas-smart-arm/calibration
ATLAS_MOCK=false
VISION_MOCK=false
ARM_MOCK=false
```
