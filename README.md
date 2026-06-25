# Atlas Arm for Smart Power O&M
> 基于华为Atlas 200I DK智能机械臂的电力智能运维/电力库房管理系统

本项目为实践题目8的开发仓库。项目基于**华为 Atlas 200I DK 开发者套件**与**智能机械臂**，针对电力场景（电子元器件、电力金具、工具等）实现目标识别、精准抓取、堆叠与移动，并构建一套可视化的电力智能运维与库房管理系统。

---

## 🛠️ 技术栈建议 (Tech Stack)
* **边缘计算平台**：Huawei Atlas 200I DK (Ascend 310 AI处理器)
* **AI 框架与工具**：MindSpore / PyTorch, Ascend Toolkit (CANN), OpenCV
* **目标识别算法**：YOLOv5 / YOLOv8 (转换为 OM 模型加速推理)
* **机械臂控制**：Python / C++, 串口通信 (Modbus/自定义协议)
* **可视化系统**：Python PyQt6 / Web 端前端（如 Vue3/React + Go/Python 后端）

---

## 📌 核心功能与模块 (Modules)

根据实践内容要求，项目划分为以下四大核心模块：

### 1. 硬件部署与基础控制 (`hardware & control`)
* **机械臂安装部署**：环境配置、固件烧录、基础通信链路调通。
* **机械臂控制算法**：实现逆运动学求解，控制机械臂精准移动到指定三维坐标。

### 2. 边缘端 AI 目标识别 (`ai & vision`)
* **色块识别**：基础颜色空间分割（HSV）与轮廓检测，用于前期抓取测试。
* **电力目标检测**：采集**电子元器件、电力金具、工具**的数据集，使用深度学习模型进行训练，并将其部署在 Atlas 200I DK 上进行硬件加速推理。

### 3. 闭环抓取与堆叠系统 (`perception & manipulation`)
* **手眼标定**：完成相机坐标系到机械臂坐标系的转换。
* **智能抓取**：结合目标识别定位与机械臂控制，实现对特定电力物资的自动识别、精准抓取、移动与分类堆叠。

### 4. 可视化管理系统 (`management system`)
* **电力库房管理**：入库/出库物资自动登记，盘点库存状态。
* **智能运维监控**：实时视频流传输、目标识别结果可视化展示、机械臂运行状态监控。

---

## 📂 目录结构预测 (Directory Structure)
```text
├── .gitignore
├── README.md
├── docs/                  # 项目文档、图片、实验报告
├── src/
│   ├── hardware/          # 机械臂驱动与基础控制脚本
│   ├── vision/            # 目标识别算法、模型转换（.om）与推理代码
│   ├── integration/       # 识别与抓取闭环控制逻辑
│   └── backend/           # 可视化系统后端代码
└── frontend/              # 可视化系统前端界面
```

---

## 首版可运行骨架

当前仓库已经包含一个无硬件可运行的 Mock 前后端：

* 后端：`FastAPI`，位于 `src/backend/`，包含统一响应格式、错误码、Mock 视觉/机械臂/任务/库存服务。
* 前端：`React + TypeScript + Vite`，位于 `frontend/`，通过统一 API client 调用后端。
* 接口契约：`docs/api/openapi.yaml`。
* 测试：`tests/contract/` 与 `tests/unit/` 覆盖后端契约、坐标转换和任务状态机；`frontend/src/api/client.test.ts` 覆盖前端 API 解包。

### 后端启动

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8080 --reload
```

或使用脚本：

```bash
./scripts/run_backend.sh
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

或使用脚本：

```bash
./scripts/run_frontend.sh
```

前端默认访问 `http://localhost:5173`，后端默认访问 `http://localhost:8080`。如需修改后端地址，可在前端设置：

```bash
VITE_API_BASE_URL=http://localhost:8080 npm run dev
```

### 真机默认程序 Demo

本分支支持“本地前端 + 开发板后端 + 开发板默认 ROS2 程序”的真机 demo。

开发板后端在 `192.168.137.100` 上运行：

```bash
./scripts/run_board_backend.sh
```

本地前端默认连接开发板后端：

```bash
./scripts/run_frontend_board.sh
```

真机模式使用开发板已有 ROS2 默认程序：

```bash
ros2 launch robot_arm_bringup block_cls_bringup.launch.py
ros2 launch robot_arm_bringup color_stacking_bringup.launch.py
```

注意事项：

* 任务运行时不另开实时视频流，避免抢占默认程序内部打开的 `/dev/video0`。
* “拍照”页面会在进入页面时连接 `/api/v1/camera/preview.mjpg` 进行 MJPEG 实时预览，离开页面后浏览器断开流，后端自动释放摄像头。
* 拍照接口会把图片保存到 `CAPTURE_DIR`，默认 `data/captures`。拍照记录只作为样本采集，不自动写入库存或任务结果。
* 开发板真实任务运行中会拒绝预览和拍照；拍照预览占用摄像头时也会拒绝启动真实任务。
* 管理面板只记录任务运行和日志，不自动写入“某物品已放入某位置”的伪结果。
* 仓库和脚本不保存 SSH 密码；需要登录开发板时请在本机 SSH 环境中处理凭据。

### 验证命令

```bash
.venv/bin/python -m pytest
cd frontend && npm test && npm run build
```
