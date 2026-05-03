# Z-Image × ComfyUI 本地文生图 · 日常操作指南

> 适用配置：RTX 4090 / Windows / Z-Image-Turbo & Base 模型  
> 开发来源：阿里巴巴通义实验室（Tongyi-MAI）  
> 更新时间：2026 年 4 月  
> 参考来源：ComfyUI 官方文档、HuggingFace、GitHub Tongyi-MAI/Z-Image

---

## 目录

1. [Z-Image 模型家族总览](#1-z-image-模型家族总览)
2. [Z-Image vs FLUX：关键差异对比](#2-z-image-vs-flux关键差异对比)
3. [模型下载与文件放置](#3-模型下载与文件放置)
4. [ComfyUI 首次配置](#4-comfyui-首次配置)
5. [基础文生图工作流（Turbo）](#5-基础文生图工作流turbo)
6. [关键采样参数说明](#6-关键采样参数说明)
7. [Z-Image Power Nodes 专属插件](#7-z-image-power-nodes-专属插件)
8. [LoRA 使用方法](#8-lora-使用方法)
9. [ControlNet 控制生成](#9-controlnet-控制生成)
10. [Z-Image-Edit 图片编辑用法](#10-z-image-edit-图片编辑用法)
11. [提示词写法建议](#11-提示词写法建议)
12. [性能优化技巧（4090 专项）](#12-性能优化技巧4090-专项)
13. [常见问题与排查](#13-常见问题与排查)
14. [资源推荐](#14-资源推荐)

---

## 1. Z-Image 模型家族总览

Z-Image 是阿里巴巴通义实验室开源的高效图像生成模型家族，核心特点是 **6B 参数、极速推理、中英双语文字渲染精准**，在 RTX 4090 上约 2–5 秒出一张图。

| 变体 | 适用场景 | 步数 | 特点 |
|------|---------|------|------|
| **Z-Image-Turbo** | 主力日常生成 | 8–9 步 | 最快，质量强，不支持负向提示词 |
| **Z-Image-Base** | LoRA 训练基础 / 高质量生成 | 20–30 步 | 非蒸馏版，支持负向提示词，社区微调首选 |
| **Z-Image-Edit** | 图片编辑 / 指令修改 | 20–30 步 | 支持自然语言指令精确编辑图片 |

> 📌 日常生图推荐用 **Z-Image-Turbo**；需要训练 LoRA 或精细控制用 **Z-Image-Base**；图片再编辑用 **Z-Image-Edit**。

---

## 2. Z-Image vs FLUX：关键差异对比

| 对比项 | Z-Image-Turbo | FLUX.1 Dev |
|--------|--------------|------------|
| 参数量 | 6B | 12B |
| 推荐步数 | 8–9 步 | 20–30 步 |
| CFG/Guidance | 0.0（固定为 0） | 3.5–4.5 |
| 全精度 VRAM | ~12GB（BF16） | ~24GB（FP16） |
| 出图速度（4090） | 约 2–3 秒 | 约 15–25 秒 |
| 中文文字渲染 | ✅ 原生支持，极准 | ⚠️ 较弱 |
| 负向提示词 | ❌ Turbo 不支持 | ⚠️ 效果有限 |
| 开源协议 | Apache 2.0 | FLUX.1 Dev 协议 |

---

## 3. 模型下载与文件放置

### 需要下载的文件

从 HuggingFace 下载以下文件（共约 12–14 GB BF16 / 约 6 GB FP8）：

#### 方式一：BF16 精度（推荐，4090 显存够用）

```
# 主扩散模型（必须，约 12GB）
https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
→ 下载：zimage_turbo_bf16.safetensors
→ 保存至：ComfyUI/models/diffusion_models/

# 文本编码器（必须）
→ 下载：clip_l.safetensors  → models/clip/
→ 下载：mt5_xl_fp16.safetensors  → models/clip/   （Z-Image 使用 mT5 多语言编码器）

# VAE（必须）
→ 下载：ae.safetensors  → models/vae/
```

#### 方式二：FP8 精度（节省约一半 VRAM，约 6GB）

```
→ 下载：zimage_turbo_fp8.safetensors
→ 保存至：ComfyUI/models/diffusion_models/
```

> ⚠️ 注意：部分早期测试报告显示 BF16 版本在某些工作流中可能生成黑图，建议优先尝试 FP8 版本，问题更少。

### 目录结构参考

```
ComfyUI/
├── models/
│   ├── diffusion_models/
│   │   └── zimage_turbo_bf16.safetensors    ← 主模型
│   ├── clip/
│   │   ├── clip_l.safetensors               ← CLIP 文本编码器
│   │   └── mt5_xl_fp16.safetensors          ← mT5 多语言编码器（支持中文）
│   ├── vae/
│   │   └── ae.safetensors                   ← VAE 解码器
│   ├── loras/
│   │   └── （LoRA 文件放这里）
│   └── controlnet/
│       └── zimage_controlnet_union.safetensors  ← ControlNet（可选）
```

---

## 4. ComfyUI 首次配置

### 必须：更新 ComfyUI 到最新版

Z-Image 需要较新版本的 ComfyUI 原生支持，**强烈建议更新到最新 nightly 版本**：

```
方式一（Manager 更新）：
ComfyUI Manager → Update All → 重启

方式二（命令行更新）：
cd ComfyUI
git pull
pip install -r requirements.txt
```

### 安装必要插件

通过 **ComfyUI Manager → Install Custom Nodes** 搜索安装：

| 插件名称 | 功能 | 必要性 |
|---------|------|--------|
| ComfyUI Manager | 插件管理 | 必装 |
| Z-Image Power Nodes | Z-Image 专属采样/编码节点 | 强烈推荐 |
| ComfyUI-Advanced-ControlNet | ControlNet 支持 | 可选 |
| ComfyUI-Impact-Pack | 人脸修复 ADetailer | 可选 |
| ComfyUI Essentials | 通用工具节点 | 推荐 |
| Sage Attention | 注意力机制加速 | 推荐（提速 20–40%） |

### 加载官方工作流

```
方式一：ComfyUI 界面 → Workflow Templates → 搜索"Z-Image" → 直接加载
方式二：访问 https://docs.comfy.org/tutorials/image/z-image/z-image-turbo 下载 JSON
方式三：CivitAI 搜索"Z Image Turbo Workflow"下载高星工作流
```

---

## 5. 基础文生图工作流（Turbo）

Z-Image Turbo 工作流的节点组成：

```
[DualCLIPLoader]        加载 clip_l + mt5_xl（注意 Z-Image 用 mT5，不是 T5）
      ↓
[CLIPTextEncode]        输入提示词（正向，中英文均可）
      ↓
[UNETLoader]            加载 Z-Image-Turbo 主模型
      ↓
[EmptyLatentImage]      设置输出尺寸（推荐 1024×1024）
      ↓
[KSampler]              采样节点：steps=9，cfg=0.0，sampler=euler，scheduler=simple
      ↓
[VAEDecode]             解码潜空间为图片
      ↓
[SaveImage]             保存输出
```

> 💡 使用 **Z-Image Power Nodes** 插件后，可用专属的 `Z-Sampler Turbo` 和 `Empty Z-Image Latent Image` 节点替代标准节点，自动处理宽高比和采样配置，更省心。

---

## 6. 关键采样参数说明

### Z-Image-Turbo 推荐参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| Steps（步数） | **8–9** | 9 = 实际 8 次 DiT 前向，超过无明显收益 |
| CFG Scale（cfg） | **0.0** | Turbo 固定为 0，填其他值会损害质量 |
| Sampler | **euler** | 最通用，搭配 simple scheduler |
| Scheduler | **simple** | 官方推荐 |
| Guidance Scale | **0.0** | Turbo 专属，勿改 |
| Seed | 随机 / 固定 | 固定 seed 复现结果 |

### Z-Image-Base 推荐参数（支持负向提示词）

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| Steps | **20–30** | 比 Turbo 慢但质量更可控 |
| CFG Scale | **3.5–5.0** | 与 FLUX 类似 |
| Sampler | **dpmpp_2m** | 细节更锐利 |
| Scheduler | **karras** | 配合 dpmpp 使用 |
| 负向提示词 | 支持 | 可加入常规负向描述 |

### 推荐出图尺寸

| 比例 | 尺寸 | 适用场景 |
|------|------|---------|
| 1:1 | 1024×1024 | 头像、产品图、默认首选 |
| 16:9 | 1360×768 | 壁纸、横版插图 |
| 9:16 | 768×1360 | 竖版、手机壁纸 |
| 4:3 | 1152×864 | 通用场景 |
| 2:3 | 832×1248 | 人像、卡片 |

> 💡 使用 `Empty Z-Image Latent Image` 节点可以直接选择预设宽高比，无需手动计算尺寸。

---

## 7. Z-Image Power Nodes 专属插件

该插件是 Z-Image 的最佳搭配，提供以下专属节点：

### 核心节点

| 节点名称 | 功能 |
|---------|------|
| `Z-Sampler Turbo` | 专为 Turbo 优化的采样节点，自动配置参数 |
| `Empty Z-Image Latent Image` | 支持宽高比预设选择（1:1 / 16:9 等），自动计算分辨率 |
| `Style Prompt Encoder` | 视觉风格选择器，可从预设风格（电影感/动漫/写实等）直接选择 |
| `Z-Image LoRA Loader` | 专为 Z-Image 优化的 LoRA 加载节点 |

### 安装步骤

```
ComfyUI Manager → Install Custom Nodes →
搜索"Z-Image Power Nodes" → 点击 Install → 重启 ComfyUI
双击画布空白处 → 搜索"Z-Image" → 即可看到所有专属节点
```

---

## 8. LoRA 使用方法

### Z-Image LoRA 特别注意

> ⚠️ **重要提示**：Z-Image 的 LoRA 不能使用 ComfyUI 默认的通用 `Load LoRA` 节点，强烈建议使用 **Z-Image Power Nodes** 中的专属 LoRA Loader，否则可能产生灰图、色偏等问题。

### 基础用法

1. 将 Z-Image 专用 LoRA 文件（`.safetensors`）放入 `models/loras/`
2. 在工作流中添加 `Z-Image LoRA Loader` 节点
3. 连接到主模型和 CLIP 编码器之间
4. 设置 `lora_scale`（推荐 0.6–1.0）

### 强度参考

| 强度值 | 效果 |
|--------|------|
| 0.3–0.5 | 轻微风格影响，多 LoRA 叠加时用 |
| 0.6–0.8 | 标准强度，最常用 |
| 0.9–1.0 | 强烈风格控制 |

### 推荐 LoRA：Flow-DPO（光照修复）

Z-Image-Turbo 因步数少，快速模型可能产生**平涂感、假皮肤、光影不真实**等问题，官方推荐的 **Z-Image-Turbo Photorealistic Lighting LoRA（Flow-DPO）** 可显著改善光影质量：

```
在 CivitAI 搜索："Z-Image Turbo Flow-DPO"
强度建议：0.6–0.8
```

### LoRA 下载来源

- CivitAI：搜索时在 Base Model 筛选选择 `ZImageTurbo`
- HuggingFace：搜索 `Z-Image LoRA`

---

## 9. ControlNet 控制生成

Z-Image 配套的 ControlNet Union 模型由阿里云 PAI 发布，单个模型支持 5 种控制模式：

| 控制类型 | 用途 |
|---------|------|
| **Canny** | 边缘检测，从线稿生成图片 |
| **HED** | 全局边缘检测，比 Canny 更柔和 |
| **Depth** | 深度图控制，保持空间层次感 |
| **Pose** | 人体姿态控制（OpenPose） |
| **MLSD** | 直线段检测，适合建筑/室内场景 |

### 安装步骤

```
1. 下载 ControlNet Union 模型：
   https://huggingface.co/Tongyi-MAI/Z-Image-Turbo-Fun-Controlnet-Union
   → 保存至：models/controlnet/

2. 安装插件：
   ComfyUI Manager → ComfyUI-Advanced-ControlNet

3. 在工作流中加入 ControlNet Apply 节点，选择对应控制类型
```

---

## 10. Z-Image-Edit 图片编辑用法

Z-Image-Edit 是基于 Z-Image-Base 微调的**指令驱动图片编辑**变体，支持自然语言描述来修改图片：

### 典型用法场景

- **换背景**：`"Replace the background with a snowy mountain scene"`
- **换服装**：`"Change the outfit to a red dress"`
- **局部修改**：`"Remove the glasses from the person"`
- **风格迁移**：`"Make this look like an oil painting"`

### 工作流配置

```
[LoadImage]              加载参考图
      ↓
[VAEEncode]              编码为潜空间
      ↓
[DualCLIPLoader]         加载文本编码器
      ↓
[CLIPTextEncode]         输入编辑指令（自然语言描述修改内容）
      ↓
[UNETLoader]             加载 Z-Image-Edit 模型（非 Turbo）
      ↓
[KSampler]               steps=20–30，cfg=3.5–5.0
      ↓
[VAEDecode → SaveImage]  输出结果
```

> 💡 Z-Image-Edit 用**自然语言描述变化**，不是描述最终图片的样子。例如：写 `"add sunglasses"` 而不是 `"a person wearing sunglasses"`。

---

## 11. 提示词写法建议

### Z-Image 的提示词特性

Z-Image 使用 **mT5 多语言编码器**，原生支持中英文双语提示词，中文文字渲染能力在所有本地模型中最强：

```
✅ 中文提示词直接可用：
一个年轻女性，穿着红色汉服，精致刺绣，站在阳光明媚的庭院中，
电影级光照，高细节，8K 分辨率

✅ 英文提示词（效果同样好）：
A young woman in red Hanfu with intricate embroidery, standing in a 
sunlit courtyard, cinematic lighting, highly detailed, 8K resolution

✅ 中英混合提示词：
Beautiful portrait, 穿着传统服饰, cinematic lighting, 超高画质
```

### 中文文字渲染（Z-Image 独特优势）

Z-Image-Turbo 能在图片内准确渲染中文文字，使用方法：

```
在提示词中直接描述文字内容：
"一张海报，中间有大字写着「欢迎光临」，红色字体，金色边框"
"A signboard that reads '北京欢迎你' in gold calligraphy style"
```

### 画质修饰词（Turbo 专用）

```
写实摄影类：
- photorealistic, hyperrealistic, RAW photo
- sharp focus, depth of field
- cinematic lighting, natural light, golden hour

艺术风格类：
- digital art, concept art（概念艺术）
- anime style, illustration（日系插画）
- oil painting, watercolor（油画/水彩）

构图类：
- portrait / full body / close-up（人像/全身/特写）
- aerial view / wide angle（俯视/广角）
- bokeh background（背景虚化）
```

### Turbo 的负向提示词限制

Z-Image-Turbo **不支持负向提示词**，Base 变体才支持：

```
# Base 版本可用的负向提示词：
blurry, low quality, deformed hands, bad anatomy, extra limbs,
watermark, text overlay, logo, overexposed, cartoon
```

---

## 12. 性能优化技巧（4090 专项）

### Sage Attention 加速

Sage Attention 是专为 Transformer 架构设计的注意力优化算法，对 Z-Image 效果显著：

```bash
# 安装 Sage Attention（需要 CUDA 12.x）
pip install sageattention

# ComfyUI Manager 安装"Sage Attention"插件后，
# 在节点设置中启用即可，无需额外配置
```

实测在 4090 上可提速 **20–40%**。

### 精度选择建议

| 精度 | VRAM 占用 | 速度 | 质量 | 建议 |
|------|----------|------|------|------|
| BF16 | ~12 GB | 基准 | 最佳 | 日常首选 |
| FP8 | ~6 GB | 稍快 | 接近 BF16 | 同时跑 ControlNet 时切换 |
| GGUF Q4 | ~4 GB | 最快 | 略有损失 | 低 VRAM 设备 |

### 模型编译加速（进阶）

```python
# 通过 Diffusers 调用时可开启编译（首次编译较慢，之后极快）
pipe.transformer.compile()
```

在 ComfyUI 中，安装 **torch.compile 支持节点** 后可在工作流内启用。

### 批量生成建议

4090 跑 Z-Image-Turbo，可以：
- 单次 batch size 设置为 4（同时生成 4 张）
- 总 VRAM 占用约 16–18 GB，仍在 24 GB 以内
- 效率比逐张生成提升约 3 倍

---

## 13. 常见问题与排查

### ❓ 生成全黑图

```
原因 1：BF16 模型与某些节点不兼容
解决：改用 FP8 版本模型（zimage_turbo_fp8.safetensors）

原因 2：VAE 型号错误
解决：确认使用 Z-Image 配套的 ae.safetensors，不要用 FLUX 的 VAE

原因 3：CFG 值设置错误
解决：Turbo 版 CFG 必须为 0.0
```

### ❓ 图片质量差 / 平涂感强

```
1. 安装并启用 Flow-DPO（Photorealistic Lighting LoRA）
2. 在提示词中加入光照描述：cinematic lighting / studio lighting
3. 尝试将 steps 从 8 调整到 12（Turbo 支持，但无需超过 15）
4. 换用 Z-Image-Base 获得更精细的质量控制
```

### ❓ ComfyUI 提示 Missing Model / 找不到模型

```
1. 确认模型文件在正确目录（diffusion_models/ 而非 checkpoints/）
2. 刷新 ComfyUI 页面（Ctrl+Shift+R）
3. 检查文件名是否与节点中填写的一致（大小写敏感）
4. Manager → Refresh 刷新模型列表
```

### ❓ mT5 编码器加载失败

```
Z-Image 使用 mT5（多语言 T5），不是 FLUX 的 t5xxl
确认下载的是：mt5_xl_fp16.safetensors
DualCLIPLoader 节点的 clip_type 选择 sdxl 或 custom，不要选 flux
```

### ❓ LoRA 加载后图像出现色偏/灰图

```
原因：使用了 ComfyUI 默认 LoRA 节点（与 Z-Image 不兼容）
解决：改用 Z-Image Power Nodes 中的 Z-Image LoRA Loader 节点
```

### ❓ 速度比预期慢

```
1. 确认 GPU 被正确调用（任务管理器 GPU 3D 使用率应接近 100%）
2. 安装 Sage Attention 并在工作流中启用
3. 确认 batch size 合理（过大也会降低每张平均速度）
4. 检查是否有 CPU Offloading 被意外开启（关闭可大幅提速）
```

---

## 14. 资源推荐

### 官方文档与源码

- Z-Image GitHub 仓库：https://github.com/Tongyi-MAI/Z-Image
- ComfyUI 官方 Z-Image 教程：https://docs.comfy.org/tutorials/image/z-image/z-image-turbo
- HuggingFace 模型页：https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
- ControlNet Union 模型：https://huggingface.co/Tongyi-MAI/Z-Image-Turbo-Fun-Controlnet-Union

### 工作流资源

- CivitAI 工作流：https://civitai.com/models/2170134/z-image-turbo-and-base-workflow（V6.0，含 Sage Attention 和 LoRA）
- Amazing Z-Image Workflow（GitHub）：https://github.com/martin-rizzo/AmazingZImageWorkflow
- RunComfy（Base LoRA 工作流）：https://www.runcomfy.com/comfyui-workflows/z-image-base-ai-toolkit-lora-inference-in-comfyui-training-matched-results

### 在线试用

- zimage.design：官方在线体验站，免费无需登录
- zimage.run：第三方在线试用平台

### 社区与教程

- Reddit r/ZImageAI：https://reddit.com/r/ZImageAI（专属社区）
- Reddit r/StableDiffusion：Z-Image 相关帖子持续涌现
- YouTube 推荐搜索："Z Image Turbo ComfyUI"

---

*本指南适用于 Z-Image-Turbo / Base / Edit 模型，ComfyUI 2025–2026 版本。*  
*建议关注 GitHub Tongyi-MAI/Z-Image 的 Release 页面获取最新模型更新。*
