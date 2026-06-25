# 模型训练与部署说明

版本：v0.1  
日期：2026-06-25  
适用范围：Atlas 200I DK A2、机械臂默认 YOLOv5 分拣程序、16 类垃圾检测模型训练与转换

## 1. 完成标准

一次模型训练与部署完成前，必须同时满足：

- 正常路径：能从已标注图片训练得到 `best.pt`，导出 `best.onnx`，转换得到开发板可加载的 `yolov5s_bs1.om`。
- 失败路径：训练、导出、转换任一步失败时，必须保留日志并停止部署，不覆盖开发板可用模型。
- 禁止状态：不得把类别顺序不一致的 `coco_names.txt` 和 `.om` 混用；不得未备份就覆盖开发板原模型或原程序。
- 数据一致性：训练数据 YAML、标签文件、模型输出类别顺序、开发板分类映射必须一致。
- 硬件安全：只修改模型文件和标签分类映射；除非另有明确要求，不修改机械臂抓取/投放角度、速度、夹爪参数。
- 验证要求：至少验证标签映射、ROS2 包构建、OM 模型在开发板上可被 `InferSession` 加载。

## 2. 总体流程

```text
采集图片
  -> 手工框选 YOLO 标签
  -> 整理 train/val 数据集
  -> 云机使用 YOLOv5s 迁移训练
  -> 导出 FP16 ONNX
  -> CANN ATC 转 Ascend OM
  -> 备份开发板原模型和源码
  -> 上传新 OM 与 coco_names.txt
  -> 修改标签到垃圾类别的映射
  -> 构建并验证
```

开发板不负责训练。开发板只运行转换后的 `.om` 模型做推理和机械臂控制。

## 3. 类别定义

模型当前使用 16 类，类别顺序必须固定：

| ID | 模型标签 | 中文名称 | 垃圾类别 |
| --- | --- | --- | --- |
| 0 | `Syringe` | 注射器 | 有害垃圾 |
| 1 | `Used_batteries` | 废旧电池 | 有害垃圾 |
| 2 | `Expired_cosmetics` | 过期化妆品 | 有害垃圾 |
| 3 | `Expired_tablets` | 过期药片 | 有害垃圾 |
| 4 | `Egg_shell` | 鸡蛋壳 | 厨余垃圾 |
| 5 | `Apple_core` | 苹果核 | 厨余垃圾 |
| 6 | `Watermelon_rind` | 西瓜皮 | 厨余垃圾 |
| 7 | `Fish_bone` | 鱼骨头 | 厨余垃圾 |
| 8 | `Peach_pit` | 桃核 | 厨余垃圾 |
| 9 | `Book` | 书本 | 可回收垃圾 |
| 10 | `Zip_top_can` | 易拉罐 | 可回收垃圾 |
| 11 | `Old_school_bag` | 旧书包 | 可回收垃圾 |
| 12 | `Newspaper` | 报纸 | 可回收垃圾 |
| 13 | `Toilet_paper` | 卫生纸 | 其他垃圾 |
| 14 | `Cigarette_butts` | 烟蒂 | 其他垃圾 |
| 15 | `Disposable_chopsticks` | 一次性筷子 | 其他垃圾 |

对应的 `coco_names.txt` 必须是同样顺序：

```text
Syringe
Used_batteries
Expired_cosmetics
Expired_tablets
Egg_shell
Apple_core
Watermelon_rind
Fish_bone
Peach_pit
Book
Zip_top_can
Old_school_bag
Newspaper
Toilet_paper
Cigarette_butts
Disposable_chopsticks
```

## 4. 数据集准备

推荐目录结构：

```text
garbage-detection-top-autolabel/
  images/
    train/
    val/
  labels/
    train/
    val/
  garbage_autodl.yaml
```

每张图片对应一个同名 `.txt` 标签文件，YOLO 格式如下：

```text
class_id center_x center_y width height
```

坐标全部归一化到 `0~1`。例如：

```text
0 0.5123 0.4761 0.2140 0.1885
```

标注建议：

- 框住朝上的真实垃圾主体，不要主要框侧面色块。
- 色块可以保留少量背景信息，但不要让模型主要依赖颜色。
- 每一类至少保留训练集和验证集图片，验证集不要和训练集重复。
- 图片拍摄角度、光照、距离尽量覆盖真实分拣时会出现的情况。

`garbage_autodl.yaml` 示例：

```yaml
path: /root/autodl-tmp/garbage-retrain-20260625/garbage-detection-top-autolabel
train: images/train
val: images/val

nc: 16
names:
  0: Syringe
  1: Used_batteries
  2: Expired_cosmetics
  3: Expired_tablets
  4: Egg_shell
  5: Apple_core
  6: Watermelon_rind
  7: Fish_bone
  8: Peach_pit
  9: Book
  10: Zip_top_can
  11: Old_school_bag
  12: Newspaper
  13: Toilet_paper
  14: Cigarette_butts
  15: Disposable_chopsticks
```

## 5. 云机环境

本次训练使用 GPU 云机完成，关键环境：

- Ubuntu 22.04
- NVIDIA RTX 5090
- Python 3.12
- PyTorch 2.8.0 + CUDA 12.8
- YOLOv5
- 预训练权重：`yolov5s.pt`

开发板是 ARM + Ascend NPU，不适合训练；训练建议始终放在 GPU 云机上完成。

## 6. YOLOv5 训练

进入 YOLOv5 目录后执行：

```bash
python train.py \
  --img 640 \
  --batch 16 \
  --epochs 100 \
  --data ../garbage-detection-top-autolabel/garbage_autodl.yaml \
  --weights yolov5s.pt \
  --name garbage16_top_yolov5s \
  --cache
```

参数说明：

- `--img 640`：训练输入尺寸为 640x640。
- `--batch 16`：每次训练 16 张图片；显存不足时可改小。
- `--epochs 100`：完整遍历数据集 100 轮。
- `--data`：指定数据集 YAML。
- `--weights yolov5s.pt`：使用 YOLOv5s 预训练模型迁移训练，不从零开始。
- `--cache`：缓存数据，加快训练。

训练输出目录示例：

```text
runs/train/garbage16_top_yolov5s/
  weights/
    best.pt
    last.pt
  results.csv
  confusion_matrix.png
  results.png
```

优先使用 `best.pt` 进行导出和部署。

本次训练结果：

| 指标 | 数值 |
| --- | --- |
| 验证图片数 | 48 |
| 验证实例数 | 48 |
| Precision | 0.942 |
| Recall | 1.000 |
| mAP50 | 0.995 |
| mAP50-95 | 0.611 |

注意：当前验证集较小，指标只能作为 smoke check，不能等价于真实场景稳定性。

## 7. 导出 ONNX

YOLOv5 训练出的 `best.pt` 不能直接在 Atlas 开发板上运行，需要先导出 ONNX。

推荐导出 FP16 ONNX：

```bash
python export.py \
  --weights runs/train/garbage16_top_yolov5s/weights/best.pt \
  --img 640 640 \
  --batch 1 \
  --include onnx \
  --half \
  --simplify \
  --opset 12 \
  --device 0
```

导出后应检查输入输出：

```bash
python - <<'PY'
import onnx
m = onnx.load("runs/train/garbage16_top_yolov5s/weights/best.onnx")
print("inputs:", [(i.name, [d.dim_value or d.dim_param for d in i.type.tensor_type.shape.dim], i.type.tensor_type.elem_type) for i in m.graph.input])
print("outputs:", [(o.name, [d.dim_value or d.dim_param for d in o.type.tensor_type.shape.dim], o.type.tensor_type.elem_type) for o in m.graph.output])
PY
```

期望结果：

```text
inputs: [('images', [1, 3, 640, 640], 10)]
outputs: [('output0', [1, 25200, 21], 10)]
```

这里 `21 = 4 个框坐标 + 1 个目标置信度 + 16 个类别分数`。

## 8. 安装 CANN 并转换 OM

云机如果是 x86 Linux，可安装 CANN toolkit 并使用 `atc` 转换。

本次使用的 CANN toolkit：

```text
Ascend-cann-toolkit_7.0.0_linux-x86_64.run
```

安装 ATC 组件示例：

```bash
chmod +x Ascend-cann-toolkit_7.0.0_linux-x86_64.run
./Ascend-cann-toolkit_7.0.0_linux-x86_64.run \
  --install \
  --quiet \
  --install-for-all \
  --install-path=/usr/local/Ascend \
  --whitelist=atc \
  --force
```

CANN 7.0 对 Python 环境比较挑剔。若云机默认 Python 是 3.12 或 NumPy 2.x，ATC 可能报错：

```text
np.float_ was removed in the NumPy 2.0 release
```

可切换到系统 Python 3.10，并安装兼容依赖：

```bash
apt-get update
apt-get install -y \
  python3-pip \
  python3-numpy \
  python3-scipy \
  python3-psutil \
  python3-attr \
  python3-cloudpickle \
  python3-tornado \
  python3-absl \
  python3-sympy \
  python3-jinja2

/usr/bin/python3 -m pip install synr==0.5.0
```

转换命令：

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PATH=/usr/local/Ascend/ascend-toolkit/latest/bin:/usr/local/Ascend/ascend-toolkit/latest/compiler/ccec_compiler/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
unset PYTHONHOME
export LD_LIBRARY_PATH=/usr/local/Ascend/ascend-toolkit/latest/x86_64-linux/devlib:/usr/local/Ascend/ascend-toolkit/latest/runtime/lib64/stub/x86_64:/usr/local/Ascend/ascend-toolkit/latest/runtime/lib64/stub:$LD_LIBRARY_PATH

atc \
  --model=/path/to/best.onnx \
  --framework=5 \
  --output=/path/to/yolov5s_bs1 \
  --input_format=NCHW \
  --input_shape="images:1,3,640,640" \
  --soc_version=Ascend310B4
```

成功时输出：

```text
ATC run success, welcome to the next use.
```

生成文件：

```text
yolov5s_bs1.om
```

本次模型 checksum：

```text
0cc006e1f60ca710df7aab688ba511884acfeacc3b11ffc10e385c41e2099ca2  yolov5s_bs1.om
```

## 9. 开发板部署

开发板默认 ROS2 工作区：

```text
/home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm
```

分拣包源码模型目录：

```text
ros2_ws/src/dofbot_garbage_yolov5/dofbot_garbage_yolov5/model/
```

运行时安装模型目录：

```text
ros2_ws/install/dofbot_garbage_yolov5/share/dofbot_garbage_yolov5/model/
```

部署前必须备份：

```bash
cd /home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/garbage_yolov5_before_16cls_${TS}"
mkdir -p "$BACKUP_DIR"
cp -a ros2_ws/src/dofbot_garbage_yolov5 "$BACKUP_DIR/src_dofbot_garbage_yolov5"
cp -a ros2_ws/install/dofbot_garbage_yolov5 "$BACKUP_DIR/install_dofbot_garbage_yolov5"
```

上传或复制新文件到源码模型目录：

```text
ros2_ws/src/dofbot_garbage_yolov5/dofbot_garbage_yolov5/model/yolov5s_bs1.om
ros2_ws/src/dofbot_garbage_yolov5/dofbot_garbage_yolov5/model/coco_names.txt
```

重新构建，让 `install/` 目录同步更新：

```bash
cd /home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select dofbot_garbage_yolov5
```

## 10. 分拣程序修改点

标签到垃圾类别的映射位于：

```text
ros2_ws/src/dofbot_garbage_yolov5/dofbot_garbage_yolov5/utils/garbage_grap.py
```

只应修改标签集合与分类判断，不应修改以下硬件参数：

- `grap_joint`
- `joints_down`
- `joints_uu`
- `joints_up`
- `Arm_serial_servo_write*` 的角度与耗时
- 标定文件 `XYT_config.txt`、`dp.bin`、`offset.txt`

当前映射：

```python
HAZARDOUS_LABELS = {
    "Syringe",
    "Used_batteries",
    "Expired_cosmetics",
    "Expired_tablets",
}

RECYCLABLE_LABELS = {
    "Zip_top_can",
    "Newspaper",
    "Old_school_bag",
    "Book",
}

KITCHEN_LABELS = {
    "Fish_bone",
    "Watermelon_rind",
    "Apple_core",
    "Egg_shell",
    "Peach_pit",
}

OTHER_LABELS = {
    "Cigarette_butts",
    "Toilet_paper",
    "Disposable_chopsticks",
}
```

建议使用 `name in LABEL_SET and self.move_status`，不要写成多段 `or ... and self.move_status`，否则 Python 运算符优先级可能导致 `move_status` 只约束最后一个标签。

## 11. 部署后验证

检查模型和标签是否同步：

```bash
cd /home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm/ros2_ws
sha256sum \
  src/dofbot_garbage_yolov5/dofbot_garbage_yolov5/model/yolov5s_bs1.om \
  install/dofbot_garbage_yolov5/share/dofbot_garbage_yolov5/model/yolov5s_bs1.om

wc -l \
  src/dofbot_garbage_yolov5/dofbot_garbage_yolov5/model/coco_names.txt \
  install/dofbot_garbage_yolov5/share/dofbot_garbage_yolov5/model/coco_names.txt
```

期望：

- 两个 `.om` checksum 一致。
- 两个 `coco_names.txt` 都是 16 行。

检查 OM 能被开发板加载：

```bash
cd /home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm/ros2_ws
source /usr/local/Ascend/ascend-toolkit/set_env.sh
python3 - <<'PY'
from ais_bench.infer.interface import InferSession
model = "/home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm/ros2_ws/install/dofbot_garbage_yolov5/share/dofbot_garbage_yolov5/model/yolov5s_bs1.om"
session = InferSession(0, model)
print("om load ok")
PY
```

检查程序语法：

```bash
python3 -m py_compile \
  src/dofbot_garbage_yolov5/dofbot_garbage_yolov5/utils/garbage_grap.py \
  install/dofbot_garbage_yolov5/lib/python3.10/site-packages/dofbot_garbage_yolov5/utils/garbage_grap.py
```

启动真实分拣程序：

```bash
cd /home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm/ros2_ws
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source install/setup.bash
ros2 run dofbot_garbage_yolov5 block_cls
```

注意：启动后机械臂会复位并驱动真实硬件，测试前应清空危险区域。

## 12. 常见问题

### 12.1 ATC 报 NumPy 2.x 兼容错误

原因：CANN 7.0 的 Python 组件仍使用 NumPy 1.x 接口。

处理：让 ATC 使用系统 Python 3.10 和 `python3-numpy`，不要让 PATH 优先指向 conda Python 3.12。

### 12.2 ATC 报缺少 `decorator`、`sympy`、`synr`

原因：CANN toolkit 的 TBE 依赖未完整安装。

处理：安装第 8 节列出的系统 Python 依赖，并用 pip 安装 `synr==0.5.0`。

### 12.3 模型能加载但分类名称不对

优先检查：

- `best.onnx` 是否确实是 16 类输出，即 `output0: [1, 25200, 21]`。
- `coco_names.txt` 是否 16 行且顺序和训练 YAML 一致。
- 开发板源码目录和 `install/` 目录中的标签文件是否一致。

### 12.4 训练指标很好但真机识别差

常见原因：

- 数据量太少，验证集与训练集场景过近。
- 标注框主要框到了色块或背景。
- 真机光照、角度、距离与训练图片差异大。
- 小物体如烟蒂、药片在画面中占比太小。

处理建议：

- 每类继续补采不同光照和角度样本。
- 优先增加容易混淆或 mAP50-95 较低的类别。
- 保持标注框围绕真实垃圾主体。
- 重新训练后再走完整导出和 ATC 转换流程。
