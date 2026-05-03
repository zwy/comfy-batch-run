# comfy-batch-run

基于 [ComfyUI](https://github.com/comfy-org/ComfyUI) 的批量 AI 图片生成工具，同时集成了大模型提示词批量生成功能。

## 功能概览

本项目包含两个核心功能模块：

| 模块 | 功能 |
|------|------|
| `batch-run` | 读取提示词列表，批量调用本地 ComfyUI API 生成图片并保存到本地 |
| `gen-prompts` | 提供参考示例，调用大模型（兼容 OpenAI 接口）批量生成风格一致的提示词 |

---

## 项目结构

```
comfy-batch-run/
├── config/
│   ├── settings.yaml            # ComfyUI 服务配置 & LLM API 配置
│   └── workflow_template.json   # 从 ComfyUI 导出的 workflow（API 格式）
├── prompts/
│   ├── examples.txt             # 提示词参考示例（每行一条）
│   └── input_prompts.txt        # 待生成图片的提示词列表（每行一条）
├── outputs/                     # 生成图片的保存目录
├── generator/
│   ├── comfy_client.py          # ComfyUI API 客户端（队列/轮询/下载）
│   └── batch_runner.py          # 批量生图主流程
├── prompt_tool/
│   ├── prompt_generator.py      # 调用大模型生成提示词
│   └── prompt_templates.py      # System prompt 模板
├── main.py                      # CLI 入口
└── requirements.txt
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config/settings.yaml`：

```yaml
comfyui:
  server: "127.0.0.1:8188"          # ComfyUI 服务地址
  workflow_template: "config/workflow_template.json"
  output_dir: "outputs"

llm:
  api_key: "sk-xxxxx"               # OpenAI / DeepSeek / Qwen 等 API Key
  base_url: null                    # 本地模型填写地址，如 http://localhost:11434/v1
  model: "gpt-4o-mini"
```

### 3. 准备 Workflow 模板

在 ComfyUI 界面中：
1. 打开 **设置 → 开启开发者模式**
2. 搭建你的工作流
3. 点击 **Save (API Format)** 导出 JSON
4. 将导出的文件保存为 `config/workflow_template.json`
5. 确保你的正向提示词节点（CLIPTextEncode）的 `title` 包含 `positive` 字样

---

## 使用方法

### 功能一：批量生成提示词

在 `prompts/examples.txt` 中准备参考示例（每行一条），然后执行：

```bash
python main.py gen-prompts --count 100
```

可选参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--examples` | `prompts/examples.txt` | 参考示例文件路径 |
| `--output` | `prompts/input_prompts.txt` | 生成结果保存路径 |
| `--count` | `100` | 生成条数 |

生成的提示词会自动保存到 `--output` 指定的文件，可直接用于下一步。

### 功能二：批量生图

确保 ComfyUI 已在本地启动（默认端口 8188），然后执行：

```bash
python main.py batch-run
```

可选参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--prompts` | `prompts/input_prompts.txt` | 提示词列表文件路径 |

程序会逐条读取提示词，依次提交到 ComfyUI 队列，等待生成完成后将图片下载保存到 `outputs/` 目录，文件名格式为 `0001.png`、`0002.png` 等。

---

## 典型工作流

```bash
# Step 1：写几条参考提示词到 prompts/examples.txt

# Step 2：用大模型扩展成 100 条
python main.py gen-prompts --count 100

# Step 3：检查 / 手动编辑 prompts/input_prompts.txt

# Step 4：启动 ComfyUI，然后批量生图
python main.py batch-run
```

---

## 兼容的 LLM 服务

`gen-prompts` 模块兼容所有支持 OpenAI Chat Completions 格式的服务：

- OpenAI（GPT-4o、GPT-4o-mini 等）
- DeepSeek（`base_url: https://api.deepseek.com`）
- 阿里云 Qwen（`base_url: https://dashscope.aliyuncs.com/compatible-mode/v1`）
- 本地 Ollama（`base_url: http://localhost:11434/v1`）

---

## 依赖

- Python 3.10+
- [ComfyUI](https://github.com/comfy-org/ComfyUI) 本地部署
- `requests`, `PyYAML`, `openai`
