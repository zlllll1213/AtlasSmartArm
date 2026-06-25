# 模型训练参数记录

版本：v0.1  
日期：2026-06-25  
对应文档：[MODEL_TRAINING.md](MODEL_TRAINING.md)  
适用模型：16 类垃圾检测 YOLOv5s -> ONNX -> Ascend OM

## 1. 本文用途

本文只记录本次实际训练、导出、转换用到的具体参数。  
完整流程说明见 [MODEL_TRAINING.md](MODEL_TRAINING.md)。

## 2. 训练环境参数

| 参数 | 本次取值 |
| --- | --- |
| 云机系统 | Ubuntu 22.04 |
| GPU | NVIDIA GeForce RTX 5090 |
| 显存 | 约 32 GB |
| Python | 3.12.3 |
| PyTorch | 2.8.0+cu128 |
| CUDA 是否可用 | True |
| YOLOv5 版本 | `f4afe0f` |
| 预训练权重 | `yolov5s.pt` |
| 训练工作目录 | `/root/autodl-tmp/garbage-retrain-20260625/garbage-detection-top-autodl-ready/yolov5` |
| 训练输出目录 | `runs/train/garbage16_top_yolov5s` |

## 3. 数据集参数

| 参数 | 本次取值 |
| --- | --- |
| 数据集格式 | YOLO detection |
| 图片尺寸来源 | 机械臂摄像头采集 |
| 训练图片数 | 192 |
| 验证图片数 | 48 |
| 训练标签数 | 192 |
| 验证标签数 | 48 |
| 背景图数量 | 0 |
| 损坏样本数量 | 0 |
| 类别数 `nc` | 16 |
| 训练缓存 | RAM cache |
| 训练集缓存大小 | 约 0.2 GB |

数据集 YAML：

```yaml
path: /root/autodl-tmp/garbage-retrain-20260625/garbage-detection-top-autolabel
train: images/train
val: images/val
nc: 16
```

## 4. 类别顺序参数

类别顺序必须同时用于：

- 数据集 YAML 的 `names`
- YOLO 标签文件中的 `class_id`
- 导出的模型输出维度
- 开发板 `coco_names.txt`
- 分拣程序标签映射

| ID | 标签 | 垃圾类别 |
| --- | --- | --- |
| 0 | `Syringe` | hazardous |
| 1 | `Used_batteries` | hazardous |
| 2 | `Expired_cosmetics` | hazardous |
| 3 | `Expired_tablets` | hazardous |
| 4 | `Egg_shell` | kitchen |
| 5 | `Apple_core` | kitchen |
| 6 | `Watermelon_rind` | kitchen |
| 7 | `Fish_bone` | kitchen |
| 8 | `Peach_pit` | kitchen |
| 9 | `Book` | recyclable |
| 10 | `Zip_top_can` | recyclable |
| 11 | `Old_school_bag` | recyclable |
| 12 | `Newspaper` | recyclable |
| 13 | `Toilet_paper` | other |
| 14 | `Cigarette_butts` | other |
| 15 | `Disposable_chopsticks` | other |

## 5. 训练命令参数

训练入口使用 YOLOv5 官方 Python 脚本 `train.py`，不是本项目自写的训练脚本。本项目只提供数据集、标签顺序、数据集 YAML、预训练权重和命令行参数；训练循环、loss 计算、优化器更新、验证和 checkpoint 保存都由 YOLOv5 官方脚本完成。

本次训练命令：

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

YOLOv5 日志展开后的完整训练参数：

| 参数 | 本次取值 | 说明 |
| --- | --- | --- |
| `weights` | `yolov5s.pt` | 迁移训练初始权重 |
| `cfg` | 空 | 使用权重自带模型结构 |
| `data` | `../garbage-detection-top-autolabel/garbage_autodl.yaml` | 数据集配置 |
| `hyp` | `data/hyps/hyp.scratch-low.yaml` | 超参数文件 |
| `epochs` | `100` | 训练轮数 |
| `batch_size` | `16` | batch size |
| `imgsz` | `640` | 输入尺寸 |
| `rect` | `False` | 不使用矩形训练 |
| `resume` | `False` | 不恢复旧训练 |
| `nosave` | `False` | 保存模型 |
| `noval` | `False` | 每轮验证 |
| `noautoanchor` | `False` | 启用 AutoAnchor 检查 |
| `noplots` | `False` | 生成训练图表 |
| `cache` | `ram` | 缓存图片到内存 |
| `image_weights` | `False` | 不按图片权重采样 |
| `device` | 空 | 自动选择 CUDA 设备 |
| `multi_scale` | `False` | 不启用多尺度训练 |
| `single_cls` | `False` | 多类别训练 |
| `optimizer` | `SGD` | 优化器 |
| `sync_bn` | `False` | 单卡训练，不同步 BN |
| `workers` | `8` | dataloader workers |
| `project` | `runs/train` | 输出根目录 |
| `name` | `garbage16_top_yolov5s` | 本次实验名 |
| `exist_ok` | `False` | 不覆盖同名目录 |
| `quad` | `False` | 不使用 quad dataloader |
| `cos_lr` | `False` | 不使用 cosine LR |
| `label_smoothing` | `0.0` | 不做标签平滑 |
| `patience` | `100` | early stopping patience |
| `freeze` | `[0]` | 不冻结主干层 |
| `save_period` | `-1` | 不按固定间隔另存 checkpoint |
| `seed` | `0` | 随机种子 |

## 6. 模型结构参数

| 参数 | 本次取值 |
| --- | --- |
| 基础模型 | YOLOv5s |
| 原始预训练类别数 | 80 |
| 覆盖后类别数 | 16 |
| 输入通道 | 3 |
| 输入尺寸 | 640x640 |
| 检测头 anchor | YOLOv5s 默认 anchor |
| Detect 层类别数 | 16 |
| 模型层数 | 214 layers |
| 参数量 | 7,062,781 |
| 梯度参数量 | 7,062,781 |
| 计算量 | 16.1 GFLOPs |
| 迁移参数 | 343/349 items from `yolov5s.pt` |
| AMP | enabled, checks passed |

Detect 层日志：

```text
Detect [16, [[10, 13, 16, 30, 33, 23],
             [30, 61, 62, 45, 59, 119],
             [116, 90, 156, 198, 373, 326]],
        [128, 256, 512]]
```

AutoAnchor 检查结果：

```text
5.10 anchors/target, 1.000 Best Possible Recall (BPR).
Current anchors are a good fit to dataset.
```

## 7. 优化器与学习率参数

| 参数 | 本次取值 |
| --- | --- |
| optimizer | SGD |
| initial learning rate `lr0` | 0.01 |
| final LR factor `lrf` | 0.01 |
| momentum | 0.937 |
| weight decay | 0.0005 |
| warmup epochs | 3.0 |
| warmup momentum | 0.8 |
| warmup bias LR | 0.1 |

优化器参数组：

```text
SGD(lr=0.01)
57 weight(decay=0.0)
60 weight(decay=0.0005)
60 bias
```

## 8. Loss 权重参数

| 参数 | 本次取值 | 说明 |
| --- | --- | --- |
| `box` | 0.05 | 框回归 loss 权重 |
| `cls` | 0.5 | 分类 loss 权重 |
| `cls_pw` | 1.0 | 分类 BCE positive weight |
| `obj` | 1.0 | objectness loss 权重 |
| `obj_pw` | 1.0 | objectness BCE positive weight |
| `iou_t` | 0.2 | IoU training threshold |
| `anchor_t` | 4.0 | anchor matching threshold |
| `fl_gamma` | 0.0 | focal loss gamma，0 表示不启用 |

## 9. 数据增强参数

| 参数 | 本次取值 | 说明 |
| --- | --- | --- |
| `hsv_h` | 0.015 | 色相增强 |
| `hsv_s` | 0.7 | 饱和度增强 |
| `hsv_v` | 0.4 | 亮度增强 |
| `degrees` | 0.0 | 不做旋转增强 |
| `translate` | 0.1 | 平移增强 |
| `scale` | 0.5 | 缩放增强 |
| `shear` | 0.0 | 不做错切 |
| `perspective` | 0.0 | 不做透视增强 |
| `flipud` | 0.0 | 不做上下翻转 |
| `fliplr` | 0.5 | 左右翻转概率 0.5 |
| `mosaic` | 1.0 | 启用 mosaic |
| `mixup` | 0.0 | 不启用 mixup |
| `copy_paste` | 0.0 | 不启用 copy-paste |

## 10. 训练过程参数

| 参数 | 本次取值 |
| --- | --- |
| 训练 batch 数/epoch | 12 |
| 验证 batch 数/epoch | 2 |
| 训练图片尺寸 | 640 |
| 验证图片尺寸 | 640 |
| dataloader workers | 8 |
| 初始 GPU 显存占用 | 约 3.34 GB |
| 稳定训练显存占用 | 约 3.83 GB |
| 训练开始时间 | 2026-06-25 14:33:45 +08:00 |
| 训练完成时间 | 2026-06-25 14:36:06 +08:00 |

本次数据集很小，所以训练时间非常短。后续如果数据量扩大，训练时间会随图片数量、epoch、batch size 增加。

## 11. 最终验证指标

| 类别 | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 48 | 48 | 0.942 | 1.000 | 0.995 | 0.611 |
| Syringe | 48 | 3 | 0.903 | 1.000 | 0.995 | 0.677 |
| Used_batteries | 48 | 3 | 0.938 | 1.000 | 0.995 | 0.720 |
| Expired_cosmetics | 48 | 3 | 0.936 | 1.000 | 0.995 | 0.367 |
| Expired_tablets | 48 | 3 | 0.931 | 1.000 | 0.995 | 0.813 |
| Egg_shell | 48 | 3 | 0.995 | 1.000 | 0.995 | 0.653 |
| Apple_core | 48 | 3 | 0.923 | 1.000 | 0.995 | 0.698 |
| Watermelon_rind | 48 | 3 | 0.953 | 1.000 | 0.995 | 0.440 |
| Fish_bone | 48 | 3 | 0.952 | 1.000 | 0.995 | 0.632 |
| Peach_pit | 48 | 3 | 0.933 | 1.000 | 0.995 | 0.665 |
| Book | 48 | 3 | 0.951 | 1.000 | 0.995 | 0.434 |
| Zip_top_can | 48 | 3 | 0.934 | 1.000 | 0.995 | 0.434 |
| Old_school_bag | 48 | 3 | 0.951 | 1.000 | 0.995 | 0.599 |
| Newspaper | 48 | 3 | 0.978 | 1.000 | 0.995 | 0.549 |
| Toilet_paper | 48 | 3 | 0.933 | 1.000 | 0.995 | 0.716 |
| Cigarette_butts | 48 | 3 | 0.915 | 1.000 | 0.995 | 0.743 |
| Disposable_chopsticks | 48 | 3 | 0.948 | 1.000 | 0.995 | 0.634 |

注意：每类验证集只有 3 个实例，指标偏乐观。真实评估应继续补充独立测试集。

## 12. ONNX 导出参数

导出命令：

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

| 参数 | 本次取值 |
| --- | --- |
| `weights` | `runs/train/garbage16_top_yolov5s/weights/best.pt` |
| `img` | `640 640` |
| `batch` | `1` |
| `include` | `onnx` |
| `half` | True |
| `simplify` | True |
| `opset` | 12 |
| `device` | 0 |
| 输出文件 | `best.onnx` |
| ONNX 大小 | 约 13.7 MB |

ONNX 输入输出：

| 名称 | shape | dtype |
| --- | --- | --- |
| `images` | `[1, 3, 640, 640]` | FP16 |
| `output0` | `[1, 25200, 21]` | FP16 |

## 13. CANN/ATC 转换参数

转换命令：

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PATH=/usr/local/Ascend/ascend-toolkit/latest/bin:/usr/local/Ascend/ascend-toolkit/latest/compiler/ccec_compiler/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
unset PYTHONHOME
export LD_LIBRARY_PATH=/usr/local/Ascend/ascend-toolkit/latest/x86_64-linux/devlib:/usr/local/Ascend/ascend-toolkit/latest/runtime/lib64/stub/x86_64:/usr/local/Ascend/ascend-toolkit/latest/runtime/lib64/stub:$LD_LIBRARY_PATH

atc \
  --model=/root/autodl-tmp/garbage-retrain-20260625/garbage-detection-top-autodl-ready/yolov5/runs/train/garbage16_top_yolov5s/weights/best.onnx \
  --framework=5 \
  --output=/root/autodl-tmp/garbage-retrain-20260625/yolov5s_bs1 \
  --input_format=NCHW \
  --input_shape="images:1,3,640,640" \
  --soc_version=Ascend310B4
```

| 参数 | 本次取值 |
| --- | --- |
| CANN toolkit | 7.0.0 x86_64 |
| Python for ATC | `/usr/bin/python3` |
| NumPy for ATC | 1.21.5 |
| `framework` | 5，ONNX |
| `input_format` | NCHW |
| `input_shape` | `images:1,3,640,640` |
| `soc_version` | `Ascend310B4` |
| 输出前缀 | `yolov5s_bs1` |
| 输出文件 | `yolov5s_bs1.om` |
| OM 大小 | 15,104,071 bytes |
| ATC 结果 | success |

OM checksum：

```text
0cc006e1f60ca710df7aab688ba511884acfeacc3b11ffc10e385c41e2099ca2  yolov5s_bs1.om
```

## 14. 本地产物参数

本地保存目录：

```text
/Users/Zhuanz/Projects/Machine/models/garbage-yolov5-16cls-20260625
```

| 文件 | 说明 | SHA256 |
| --- | --- | --- |
| `best.pt` | 训练出的 PyTorch checkpoint | `3aaf1684ef604cb9fd0343cb351bf75d7bcc78819fee074aa80a73ce2a7cf10f` |
| `best.onnx` | FP16 simplified ONNX | `b415e4d16b7a0dca6295c2151e4b6675163ba1b66829067a862a55bbba5792a6` |
| `yolov5s_bs1.om` | Ascend310B4 OM | `0cc006e1f60ca710df7aab688ba511884acfeacc3b11ffc10e385c41e2099ca2` |
| `coco_names_16cls.txt` | 16 类标签文件 | 见第 4 节 |

## 15. 参数调整建议

### 15.1 数据量变大

优先保持：

- `--img 640`
- `--weights yolov5s.pt`
- `--epochs 100`

可按显存调整：

- RTX 5090：`--batch 16` 或更高。
- 24 GB 显存：可尝试 `--batch 16`。
- 12 GB 显存：建议 `--batch 8`。
- 8 GB 显存：建议 `--batch 4`。

### 15.2 真机误检多

优先改数据，不要先调模型结构：

- 增加误检类别的真实场景图片。
- 增加不同光照、距离、角度样本。
- 保证标注框围绕朝上的垃圾主体。
- 单独留出独立测试集，不参与训练和验证。

### 15.3 小物体识别差

可以尝试：

- 提高拍摄分辨率后再裁剪/缩放到 640。
- 增加小物体近距离样本。
- 训练时保持 `--img 640`，数据明显增多后再考虑 `--img 960`。

注意：如果改成更大输入尺寸，开发板程序、ONNX 导出和 ATC `input_shape` 也必须同步变化。

### 15.4 类别增加或删减

必须同步修改：

- 数据集 YAML `nc` 和 `names`
- 标注文件里的 `class_id`
- `coco_names.txt`
- 分拣程序标签集合
- 后端日志解析类别映射
- ONNX 输出维度预期
- 开发板部署文档
