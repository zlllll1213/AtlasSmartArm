# AtlasSmartArm 产品需求文档

版本：v0.2  
日期：2026-06-25  
状态：真机 demo 阶段

## 1. 背景

AtlasSmartArm 连接华为 Atlas 200I DK 开发板、USB 摄像头和机械臂，提供一个可视化工作台。当前阶段不重写开发板默认 ROS2 分拣/堆叠程序，而是通过后端适配层从前端启动这些默认程序，并展示任务状态、ROS 日志、拍照样本和分拣识别标签。

第一版验收目标不是完整自动库存系统，而是稳定完成真机 demo：

- 浏览器能启动/中断开发板默认分拣和堆叠程序。
- 默认程序运行日志能实时进入任务详情和事件流。
- 分拣程序输出标签时，前端能展示识别结果。
- 拍照页面能独占摄像头预览并采集样本。
- 任务运行与拍照预览不会抢占同一个摄像头。

## 2. 用户与场景

| 用户 | 场景 | 目标 |
| --- | --- | --- |
| 演示操作者 | 课堂/答辩现场 | 从浏览器启动分拣/堆叠并观察状态 |
| 模型训练者 | 样本采集 | 打开实时预览，给新物体拍照并输入标签 |
| 开发者 | 真机联调 | 查看 ROS 日志、错误和识别标签 |
| 项目维护者 | 后续扩展 | 在不破坏默认程序的前提下接入新模型和结构化结果 |

## 3. 范围

### 3.1 当前范围内

- 本地 React 前端工作台。
- 开发板 FastAPI 后端。
- Board 模式启动默认 ROS2 分拣/堆叠程序。
- Mock 模式用于本地开发。
- 任务状态、日志、退出码、启动/结束时间。
- 分拣识别标签展示。
- 摄像头 MJPEG 预览和拍照保存。
- 管理页任务记录和事件流。
- 系统状态页。

### 3.2 当前范围外

- 不修改开发板默认 ROS2 程序源码。
- 不在真实任务运行中展示实时分拣画面。
- 不把默认程序日志自动写成库存入库/出库结果。
- 不实现真实权限系统。
- 不上传 SSH 密码、模型权重或拍照样本到仓库。
- 不实现机械臂急停；当前 cancel 只是对 ROS2 进程发送 `SIGINT`。

## 4. 核心需求

### R1 分拣任务

用户在分拣页点击启动后：

- 前端调用 `POST /api/v1/tasks/pick-sort`。
- Board 模式下后端启动：

```bash
ros2 launch robot_arm_bringup block_cls_bringup.launch.py
```

- 后端加载 Ascend 环境和 ROS2 工作区环境。
- 任务进入运行状态，页面展示任务 ID、状态、PID、日志和进度。
- 如果已有任务运行，返回 `ARM_BUSY`。
- 如果摄像头预览活跃，返回 `CAMERA_BUSY`。

成功标准：

- 默认程序能启动。
- 日志持续进入任务详情。
- 不出现 `libascendcl.so` 环境错误。

### R2 分拣识别结果

当默认分拣程序输出：

```text
msg is: {'Book': (0.012, 0.321)}
new msg is [('Book', (0.012, 0.321))]
```

后端解析为结构化字段：

- `latest_label`
- `latest_category`
- `detections`
- `updated_at`

前端分拣页展示：

- 最新标签。
- 垃圾类别中文说明。
- 检测列表和坐标。
- 无结果时显示等待状态。

失败标准：

- 无法解析或无关日志不得生成假结果。
- 未知标签必须标记为 `unknown`。

### R3 堆叠任务

用户在堆叠页点击启动后：

- 前端调用 `POST /api/v1/tasks/stack`。
- Board 模式下后端启动：

```bash
ros2 launch robot_arm_bringup color_stacking_bringup.launch.py
```

- 页面展示任务状态和 ROS 日志。
- 同样遵守单任务锁和摄像头互斥。

### R4 任务取消

用户点击中断后：

- 前端调用 `POST /api/v1/tasks/{task_id}/cancel`。
- 后端对 ROS2 进程组发送 `SIGINT`。
- 任务标记为 `cancelled`。
- 页面明确提示这不是机械臂急停。

### R5 拍照与实时预览

用户进入拍照页：

- 前端加载 `/api/v1/camera/preview.mjpg`。
- 后端打开摄像头并输出 MJPEG 流。
- 用户输入标签并点击拍照，后端保存图片到 `CAPTURE_DIR`。
- 页面展示最近照片列表。

用户离开拍照页：

- 前端移除图片流并调用 `/api/v1/camera/preview/stop`。
- 后端释放摄像头。

互斥规则：

- active task 存在时，预览/拍照返回 `ARM_BUSY`。
- preview active 时，真实任务创建返回 `CAMERA_BUSY`。

### R6 管理与状态

管理页：

- 显示任务记录。
- 显示 WebSocket 事件流。
- 不展示伪库存结果。

状态页：

- 显示开发板 host、program mode、camera policy、camera preview 状态、active task、模型名、标定状态。

## 5. 非功能需求

### 5.1 安全

- 不保存 SSH 密码。
- 不在任务运行时抢占摄像头。
- 不绕过后端任务服务直接控制硬件。
- cancel 不冒充 emergency stop。
- 后端启动 ROS2 程序前必须加载 Ascend 环境。

### 5.2 可维护性

- API 字段在 OpenAPI、后端响应、前端类型和测试中保持一致。
- 默认程序适配层只处理启动、日志、退出码和环境，不掺入 UI 逻辑。
- 识别解析只处理稳定格式，不猜测未知日志。

### 5.3 可测试性

- 后端使用 FakeProgramRunner 测试真实任务状态转换。
- 摄像头服务使用 FakeCameraBackend 测试释放和互斥。
- 前端 API client 测试覆盖新增任务字段。
- 不依赖真实机械臂才能跑单元/契约测试。

## 6. 当前系统接口

完整定义见 `docs/api/openapi.yaml`。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/health` | 健康检查 |
| `GET` | `/api/v1/system/status` | 系统状态 |
| `POST` | `/api/v1/tasks/pick-sort` | 启动分拣 |
| `POST` | `/api/v1/tasks/stack` | 启动堆叠 |
| `GET` | `/api/v1/tasks/{task_id}` | 查询任务 |
| `POST` | `/api/v1/tasks/{task_id}/cancel` | 中断任务 |
| `GET` | `/api/v1/camera/status` | 摄像头状态 |
| `GET` | `/api/v1/camera/preview.mjpg` | MJPEG 预览 |
| `POST` | `/api/v1/camera/preview/stop` | 停止预览 |
| `POST` | `/api/v1/camera/captures` | 拍照 |
| `WS` | `/ws/v1/events` | 事件流 |

## 7. 任务详情模型

关键字段：

```json
{
  "task_id": "task_000000000001",
  "type": "pick_sort",
  "state": "moving",
  "program": "pick_sort_default",
  "pid": 12345,
  "exit_code": null,
  "logs": [],
  "recognition": null,
  "started_at": "2026-06-25T00:00:00Z",
  "ended_at": null
}
```

`recognition` 示例：

```json
{
  "latest_label": "Book",
  "latest_category": "recyclable",
  "detections": [
    {"label": "Book", "category": "recyclable", "x_m": 0.012, "y_m": 0.321, "source": "msg"}
  ],
  "updated_at": "2026-06-25T00:00:01Z"
}
```

## 8. 验收清单

### 本地验收

- `.venv/bin/python -m pytest tests` 通过。
- `cd frontend && npm test -- --run` 通过。
- `cd frontend && npm run build` 通过。
- `bash -n scripts/run_board_backend.sh` 通过。

### 真机验收

- 开发板后端 `GET /api/v1/system/status` 返回 `program_mode=board`。
- 前端 `http://127.0.0.1:5173` 能访问开发板后端。
- 打开拍照页可看到预览，离开后摄像头释放。
- 拍照预览时启动分拣/堆叠被阻止。
- 启动分拣时不再出现 `libascendcl.so`。
- 分拣日志输出识别结果后，前端识别窗口显示标签。
- 管理页只显示任务记录，不写伪库存。

## 9. 后续迭代

### I1 结构化 ROS2 输出

让默认程序或 wrapper 输出 JSON 行，例如：

```json
{"type":"recognition","label":"Book","category":"recyclable","x_m":0.012,"y_m":0.321}
```

这样可以减少日志解析脆弱性。

### I2 训练模型接入

用户训练完成新 YOLO/OM 模型后：

- 上传模型和标签文件到开发板。
- 更新默认程序模型路径或启动参数。
- 同步标签类别映射。
- 补充新标签测试。

### I3 真实库存联动

只有当默认程序能输出结构化、可验证的放置结果时，才允许自动写库存/库位。

### I4 急停能力

增加独立硬件急停接口和 UI，不与任务 cancel 混淆。

### I5 部署固化

将开发板后端做成 systemd 服务，固定环境变量、日志路径和重启策略。
