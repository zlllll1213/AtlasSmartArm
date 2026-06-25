# AtlasSmartArm

AtlasSmartArm 是一套用于华为 Atlas 200I DK 与机械臂联调的 Web demo。当前版本以“本地前端 + 开发板后端 + 开发板默认 ROS2 程序”为核心，目标是让操作者可以从浏览器启动分拣/堆叠、查看 ROS 日志、采集训练样本照片，并观察默认分拣程序输出的识别标签。

本仓库不修改开发板默认 ROS2 程序源码。后端只负责启动、停止、记录日志和解析稳定输出；真实机械臂动作仍由开发板已有程序执行。

## 当前能力

- 分拣：前端调用后端启动 `robot_arm_bringup block_cls_bringup.launch.py`。
- 堆叠：前端调用后端启动 `robot_arm_bringup color_stacking_bringup.launch.py`。
- 单任务锁：真实任务同一时刻只允许一个运行，重复启动会返回 `ARM_BUSY`。
- 摄像头互斥：真实任务运行时不开放预览/拍照；拍照预览占用摄像头时也禁止启动真实任务。
- 识别结果展示：后端解析默认分拣程序日志中的 `msg is: {...}` 和 `new msg is [...]`，前端展示最新标签、垃圾类别和检测列表。
- 拍照工作台：进入拍照页时打开 MJPEG 预览，离开页面后浏览器断开流，后端释放摄像头。
- 管理面板：记录任务运行、日志和事件流，不伪造“物品已入库/已放置”的业务结果。
- 系统状态：展示开发板、摄像头、机械臂、模型、标定、当前任务和摄像头策略。

## 运行拓扑

```text
Browser on local machine
  http://127.0.0.1:5173
        |
        | REST + WebSocket
        v
Backend on Atlas board
  http://192.168.137.100:8080
        |
        | subprocess + ROS2 env
        v
Board default ROS2 programs
  robot_arm_bringup block_cls_bringup.launch.py
  robot_arm_bringup color_stacking_bringup.launch.py
```

## 技术栈

- 前端：React, TypeScript, Vite, lucide-react
- 后端：FastAPI, Python 3.10+
- 通信：REST API, WebSocket events, MJPEG preview stream
- 硬件端：Ubuntu 22.04, ROS2 Humble, Ascend Toolkit/CANN, Atlas 200I DK, USB camera, mechanical arm
- 测试：pytest, Vitest, TypeScript build

## 目录结构

```text
.
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDE.md
│   ├── PRD.md
│   └── api/openapi.yaml
├── frontend/
│   └── src/
├── scripts/
│   ├── run_backend.sh
│   ├── run_board_backend.sh
│   ├── run_frontend.sh
│   └── run_frontend_board.sh
├── src/
│   ├── backend/
│   ├── hardware/
│   ├── integration/
│   └── vision/
└── tests/
    ├── contract/
    └── unit/
```

## 本地 Mock 模式

Mock 模式不连接真实开发板或机械臂，适合前端开发和接口调试。

```bash
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://localhost:8080`

## 真机 Demo 模式

真机模式推荐后端部署在开发板，前端运行在本地开发机。

开发板后端：

```bash
./scripts/run_board_backend.sh
```

本地前端连接开发板：

```bash
./scripts/run_frontend_board.sh
```

等价手动命令：

```bash
cd frontend
VITE_API_BASE_URL=http://192.168.137.100:8080 npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

## 开发板后端关键配置

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `PROGRAM_MODE` | `mock` | `board` 时启动真实默认 ROS2 程序 |
| `APP_PORT` | `8080` | 后端监听端口 |
| `ROBOT_ARM_ROOT` | `/home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm` | 机械臂 ROS2 工作区根目录 |
| `ASCEND_TOOLKIT_SET_ENV` | `/usr/local/Ascend/ascend-toolkit/set_env.sh` | Ascend 动态库环境脚本 |
| `CAPTURE_DIR` | `data/captures` | 拍照样本保存目录 |
| `CAMERA_INDEX` | `0` | 摄像头设备索引 |
| `CAMERA_WIDTH` | `640` | 预览/拍照宽度 |
| `CAMERA_HEIGHT` | `480` | 预览/拍照高度 |

后端启动默认程序时会显式加载 Ascend 环境，再加载机械臂工作区环境：

```bash
. "$ASCEND_TOOLKIT_SET_ENV"
. "$ROBOT_ARM_ROOT/setenv.sh"
ros2 launch ...
```

这样可以避免非交互式后端进程缺少 `libascendcl.so`。

## 默认程序与摄像头策略

真实分拣/堆叠任务运行时，默认 ROS2 程序会独占 `/dev/video0`。因此项目约定：

- 分拣/堆叠页面不主动打开视频流。
- 任务运行中，拍照和实时预览接口返回 `ARM_BUSY`。
- 拍照预览中，启动真实任务返回 `CAMERA_BUSY`。
- 取消任务只发送 `SIGINT` 给 ROS2 进程组，不等同于机械臂急停。

## 识别标签展示

板端默认分拣程序当前会输出类似日志：

```text
msg is: {'Book': (0.012, 0.321)}
new msg is [('Book', (0.012, 0.321))]
```

后端解析这些日志并写入任务详情：

```json
{
  "recognition": {
    "latest_label": "Book",
    "latest_category": "recyclable",
    "detections": [
      {"label": "Book", "category": "recyclable", "x_m": 0.012, "y_m": 0.321, "source": "msg"}
    ],
    "updated_at": "2026-06-25T00:00:00Z"
  }
}
```

当前类别映射来自开发板默认分拣代码：

- `hazardous`：Syringe, Used_batteries, Expired_cosmetics, Expired_tablets
- `recyclable`：Zip_top_can, Newspaper, Old_school_bag, Book
- `kitchen`：Fish_bone, Watermelon_rind, Apple_core, Egg_shell, Peach_pit
- `other`：Cigarette_butts, Toilet_paper, Disposable_chopsticks
- 未知标签：`unknown`

## 主要接口

完整接口以 [docs/api/openapi.yaml](docs/api/openapi.yaml) 为准。

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

## 验证命令

后端：

```bash
.venv/bin/python -m pytest tests
```

前端：

```bash
cd frontend
npm test -- --run
npm run build
```

开发板最小环境验证：

```bash
cd /home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm
bash -lc '. /usr/local/Ascend/ascend-toolkit/set_env.sh && . ./setenv.sh && python3 -c "import aclruntime; print(\"aclruntime import ok\")"'
```

## 安全约束

- 仓库中不保存 SSH 密码、token、密钥或开发板私有凭据。
- 不在默认程序任务运行中打开额外摄像头流。
- 不把默认程序日志推断成真实库存变更。
- 不直接从前端下发舵机底层控制指令。
- 合并和推送前必须确认测试通过、工作区无无关改动。
