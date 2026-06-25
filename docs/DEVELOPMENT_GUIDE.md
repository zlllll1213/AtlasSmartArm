# AtlasSmartArm 开发指南

版本：v0.2  
日期：2026-06-25  
适用范围：本地前端、开发板后端、开发板默认 ROS2 机械臂程序联调

## 1. 完成标准

任何功能提交前必须同时满足：

- 正常路径：用户能在前端完成目标操作，并得到明确状态反馈。
- 失败路径：设备忙、摄像头被占用、任务重复启动、程序启动失败时有明确错误。
- 禁止状态：不得伪造识别结果、库存位置或任务成功结果。
- 数据一致性：任务状态、日志、识别结果、事件流来自同一个任务 ID。
- 硬件安全：真实任务同一时刻只能有一个；摄像头预览和默认程序不能同时占用摄像头。
- 测试要求：后端契约/单元测试、前端 API 测试、前端构建必须通过。

## 2. 架构边界

```text
frontend/
  React 工作台：分拣、堆叠、拍照、管理、状态

src/backend/
  FastAPI：统一响应、任务服务、默认程序适配、摄像头服务、事件流

src/integration/
  Mock 状态机、坐标转换等可测试逻辑

src/vision/
  本地 Mock 视觉与后续模型接入位置

src/hardware/
  机械臂硬件适配预留位置

Board ROS2 workspace
  开发板已有默认分拣/堆叠程序，本项目通过进程启动适配
```

允许调用方向：

```text
Frontend -> Backend REST/WebSocket -> Board program adapter -> ROS2 default program
```

禁止：

- 前端直接 SSH、ROS2、串口或访问开发板文件。
- 后端绕过任务服务直接修改任务状态。
- 视觉/日志解析代码直接修改库存。
- 在真实任务运行中另开 `/dev/video0`。

## 3. 运行模式

### 3.1 Mock 模式

适合本地开发，不连接真实硬件。

```bash
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

### 3.2 Board 模式

适合真机 demo。后端运行在开发板，前端运行在本地。

```bash
# board
PROGRAM_MODE=board ./scripts/run_board_backend.sh

# local
./scripts/run_frontend_board.sh
```

前端通过 `VITE_API_BASE_URL=http://192.168.137.100:8080` 访问开发板后端。

## 4. 关键配置

| 配置项 | 默认值 | 使用位置 |
| --- | --- | --- |
| `PROGRAM_MODE` | `mock` | 后端服务容器 |
| `APP_PORT` | `8080` | 后端监听端口 |
| `ROBOT_ARM_ROOT` | `/home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm` | 默认程序适配层 |
| `ASCEND_TOOLKIT_SET_ENV` | `/usr/local/Ascend/ascend-toolkit/set_env.sh` | 默认程序启动前加载 Ascend 环境 |
| `CAPTURE_DIR` | `data/captures` | 拍照服务 |
| `CAMERA_INDEX` | `0` | 摄像头服务 |
| `CAMERA_WIDTH` | `640` | 摄像头服务 |
| `CAMERA_HEIGHT` | `480` | 摄像头服务 |

不要把 SSH 密码、GitHub token、私钥或其他凭据写进仓库。

## 5. 后端开发规范

### 5.1 统一响应

所有 HTTP API 返回统一 envelope：

```json
{
  "request_id": "req_xxx",
  "success": true,
  "data": {},
  "error": null
}
```

失败响应：

```json
{
  "request_id": "req_xxx",
  "success": false,
  "data": null,
  "error": {
    "code": "ARM_BUSY",
    "message": "A board default program task is already running.",
    "details": {"active_task_id": "task_000000000001"}
  }
}
```

### 5.2 任务服务不变量

- Board 模式下只能有一个未结束任务。
- 创建真实任务前必须检查摄像头预览是否活跃。
- 任务取消只发送 `SIGINT`，前端文案必须说明它不是机械臂急停。
- 进程 stdout/stderr 必须写入任务 `logs` 并发布 `task.log.created`。
- 进程退出码 `0` 映射为 `succeeded`，非零映射为 `failed`。
- 默认程序任务不得自动修改库存。

### 5.3 默认程序启动

启动命令由 `src/backend/services/board_program_runner.py` 生成。

分拣：

```bash
ros2 launch robot_arm_bringup block_cls_bringup.launch.py
```

堆叠：

```bash
ros2 launch robot_arm_bringup color_stacking_bringup.launch.py
```

启动前必须加载：

```bash
. "$ASCEND_TOOLKIT_SET_ENV"
. ./setenv.sh
```

这是为了保证非交互式后端进程也能找到 `libascendcl.so`。

### 5.4 识别日志解析

只解析默认程序已知稳定格式：

```text
msg is: {'Book': (0.012, 0.321)}
new msg is [('Book', (0.012, 0.321))]
```

实现要求：

- 使用 `ast.literal_eval`，禁止 `eval`。
- 无法解析时保持 `recognition=null`，不能造假。
- 未知标签类别为 `unknown`。
- 识别结果只展示，不写库存。

### 5.5 摄像头服务

- `/api/v1/camera/preview.mjpg` 打开 MJPEG 流。
- `/api/v1/camera/preview/stop` 主动释放预览。
- 页面离开拍照页时前端必须断开图片流并调用 stop。
- 有 active task 时，拍照和预览必须返回 `ARM_BUSY`。
- 预览活跃时，真实任务创建必须返回 `CAMERA_BUSY`。

## 6. 前端开发规范

### 6.1 页面结构

当前工作台包含：

- 分拣页：启动/中断默认分拣程序、查看识别结果、查看 ROS 日志。
- 堆叠页：启动/中断默认堆叠程序、查看 ROS 日志。
- 拍照页：实时预览、输入标签、保存样本、查看最近照片。
- 管理页：任务记录和事件流。
- 状态页：开发板、摄像头、机械臂、模型、标定状态。

### 6.2 API 类型

- API 类型维护在 `frontend/src/api/types.ts`。
- 请求封装维护在 `frontend/src/api/client.ts`。
- 组件不得直接拼接未声明字段。
- 新增后端字段必须同步更新 API client 测试。

### 6.3 UI 约束

- 日志、事件流、任务记录、照片列表使用滚动框，不撑高整页。
- 真实任务页面不展示摄像头实时流，只说明摄像头被默认程序独占。
- 空识别结果显示等待状态，不展示模拟标签。
- 错误文案要让用户知道是设备忙、摄像头忙还是后端程序失败。

## 7. API 契约

`docs/api/openapi.yaml` 是 HTTP API 的事实来源。接口变更流程：

```text
更新 OpenAPI -> 更新后端实现 -> 更新前端类型 -> 更新测试 -> 运行验证 -> 提交
```

当前主要接口：

- `GET /api/v1/health`
- `GET /api/v1/system/status`
- `POST /api/v1/tasks/pick-sort`
- `POST /api/v1/tasks/stack`
- `GET /api/v1/tasks/{task_id}`
- `POST /api/v1/tasks/{task_id}/cancel`
- `GET /api/v1/camera/status`
- `GET /api/v1/camera/preview.mjpg`
- `POST /api/v1/camera/preview/stop`
- `POST /api/v1/camera/captures`
- `WS /ws/v1/events`

## 8. 测试策略

后端：

```bash
.venv/bin/python -m pytest tests
```

覆盖重点：

- Board 模式启动默认分拣/堆叠命令。
- 单任务锁和摄像头互斥。
- stdout/stderr 写入日志和事件。
- 退出码到任务状态映射。
- cancel 发送中断并标记取消。
- 识别日志解析和未知标签。
- 默认程序不改库存。

前端：

```bash
cd frontend
npm test -- --run
npm run build
```

覆盖重点：

- 统一响应解包。
- 任务详情扩展字段。
- 摄像头预览和图片 URL 拼接。
- TypeScript 类型检查和生产构建。

## 9. 真机验证清单

启动服务：

```bash
# board
cd /root/AtlasSmartArm-board-demo
PROGRAM_MODE=board python3 -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8080

# local
cd frontend
VITE_API_BASE_URL=http://192.168.137.100:8080 npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

检查：

- `GET /api/v1/system/status` 返回 `program_mode=board`。
- `active_task_id=null` 时才启动真实任务。
- 拍照页打开后 `preview_active=true`，退出后变为 `false`。
- 拍照预览时启动真实任务返回 `CAMERA_BUSY`。
- 真实任务运行时拍照返回 `ARM_BUSY`。
- 分拣任务日志中不再出现 `libascendcl.so` 导入错误。
- 如果默认程序输出 `msg is:` 或 `new msg is`，分拣页出现识别标签。

## 10. Git 工作流

- 功能开发使用 `codex/` 前缀分支。
- 提交前运行相关测试。
- 不提交密码、模型大文件、拍照样本和本地缓存。
- 合并到 `main` 前确认工作区干净。
- 推送 `main` 前确认本地 `main` 已包含目标分支提交。

## 11. 常见故障

### `ImportError: libascendcl.so`

原因：后端以非交互式 shell 启动 ROS2 程序，没有加载 Ascend Toolkit 环境。

处理：

```bash
. /usr/local/Ascend/ascend-toolkit/set_env.sh
python3 -c "import aclruntime"
```

确认 `ASCEND_TOOLKIT_SET_ENV` 指向正确的 `set_env.sh`。

### 8080 无法连接

检查：

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
tail -80 board-backend.log
```

### 5173 端口被占用

检查：

```bash
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

确认旧前端进程可停后再启动新服务。
