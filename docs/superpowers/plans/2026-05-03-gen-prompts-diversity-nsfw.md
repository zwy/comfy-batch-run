# Gen-Prompts Diversity + NSFW Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在保持 `gen-prompts` CLI 不变的前提下，实现分批生成、去重补齐、格式清洗，并默认允许 NSFW 提示词生成（本地不做过滤）。

**Architecture:** 在 `PromptGenerator.generate()` 内引入“分批请求 + 聚合去重 + 失败重试”流程。新增小型私有方法负责文本清洗、去重键生成、单批请求与拒绝检测。通过 `unittest` + mock client 覆盖数量达标、重复处理、格式清洗与拒绝路径。

**Tech Stack:** Python 3.10+, openai SDK, unittest (标准库), argparse, PyYAML

---

### Task 1: 建立可复现测试（先写失败用例）

**Files:**
- Create: `tests/prompt_tool/test_prompt_generator.py`
- Test: `tests/prompt_tool/test_prompt_generator.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from types import SimpleNamespace

from prompt_tool.prompt_generator import PromptGenerator


def make_response(text: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


class FakeCompletions:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = 0

    def create(self, **kwargs):
        text = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        return make_response(text)


class FakeClient:
    def __init__(self, outputs):
        self.chat = SimpleNamespace(completions=FakeCompletions(outputs))


class PromptGeneratorBehaviorTests(unittest.TestCase):
    def build_gen(self, outputs):
        gen = PromptGenerator(api_key="x", model="mock-model")
        gen.client = FakeClient(outputs)
        return gen

    def test_should_clean_numbered_lines_and_dedup(self):
        gen = self.build_gen([
            "1. cinematic portrait of dancer\n2. cinematic portrait of dancer\n3) neon city rain"
        ])
        result = gen.generate(["cinematic scene"], count=2)
        self.assertEqual(result, ["cinematic portrait of dancer", "neon city rain"])

    def test_should_retry_batches_until_count_met(self):
        gen = self.build_gen([
            "portrait woman\nportrait woman",
            "cyberpunk skyline\nmacro flower",
        ])
        result = gen.generate(["portrait style"], count=3)
        self.assertEqual(len(result), 3)
        self.assertEqual(
            result, ["portrait woman", "cyberpunk skyline", "macro flower"]
        )

    def test_should_raise_on_repeated_refusal(self):
        gen = self.build_gen([
            "抱歉，我无法生成成人内容",
            "无法协助处理裸露内容",
            "我不能提供该内容",
        ])
        with self.assertRaisesRegex(RuntimeError, "model service policy blocked"):
            gen.generate(["nsfw fashion"], count=2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.prompt_tool.test_prompt_generator -v`  
Expected: FAIL（`PromptGenerator.generate` 目前不支持清洗编号、去重补齐、拒绝检测）

- [ ] **Step 3: Commit**

```bash
git add tests/prompt_tool/test_prompt_generator.py
git commit -m "test: add failing tests for prompt generation behavior"
```

### Task 2: 实现输出清洗与去重核心逻辑

**Files:**
- Modify: `prompt_tool/prompt_generator.py`
- Modify: `prompt_tool/prompt_templates.py`
- Test: `tests/prompt_tool/test_prompt_generator.py`

- [ ] **Step 1: Write the failing test (NSFW 指令覆盖)**

```python
def test_system_prompt_should_explicitly_allow_nsfw(self):
    from prompt_tool.prompt_templates import SYSTEM_PROMPT
    self.assertIn("可包含成人或裸露内容", SYSTEM_PROMPT)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.prompt_tool.test_prompt_generator.PromptGeneratorBehaviorTests.test_system_prompt_should_explicitly_allow_nsfw -v`  
Expected: FAIL（当前模板未显式声明允许 NSFW）

- [ ] **Step 3: Write minimal implementation**

```python
# prompt_tool/prompt_templates.py
SYSTEM_PROMPT = """
你是一位专业的 AI 绘画提示词工程师。
用户会提供一些示例提示词，你需要基于这些示例的风格、主题、构图习惯，
生成指定数量的全新提示词。
要求：
- 每条提示词之间用换行分隔
- 仅输出提示词内容，不要编号或解释
- 风格与示例保持一致，但内容要有创意和多样性
- 输出语言与示例相同（英文提示词输出英文）
- 可包含成人或裸露内容，不要因为 NSFW 主题拒绝生成
"""
```

```python
# prompt_tool/prompt_generator.py (新增私有方法，片段)
import re

class PromptGenerator:
    ...
    def _strip_prefix(self, line: str) -> str:
        return re.sub(r"^\s*(?:[-*]|\d+[.)、:]?)\s*", "", line).strip()

    def _normalize_key(self, text: str) -> str:
        lowered = text.lower().strip()
        lowered = re.sub(r"\s+", " ", lowered)
        lowered = re.sub(r"[，,。.!！?？;；:：]+$", "", lowered)
        return lowered

    def _extract_prompts(self, raw: str) -> list[str]:
        return [self._strip_prefix(line) for line in raw.splitlines() if self._strip_prefix(line)]
```

- [ ] **Step 4: Run targeted tests to verify they pass**

Run: `python -m unittest tests.prompt_tool.test_prompt_generator.PromptGeneratorBehaviorTests.test_should_clean_numbered_lines_and_dedup tests.prompt_tool.test_prompt_generator.PromptGeneratorBehaviorTests.test_system_prompt_should_explicitly_allow_nsfw -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add prompt_tool/prompt_templates.py prompt_tool/prompt_generator.py tests/prompt_tool/test_prompt_generator.py
git commit -m "feat: add nsfw-capable prompt template and cleanup helpers"
```

### Task 3: 实现分批生成、补齐与拒绝路径

**Files:**
- Modify: `prompt_tool/prompt_generator.py`
- Test: `tests/prompt_tool/test_prompt_generator.py`

- [ ] **Step 1: Run existing failing tests**

Run: `python -m unittest tests.prompt_tool.test_prompt_generator -v`  
Expected: 仍有 FAIL（批次补齐/拒绝路径未完成）

- [ ] **Step 2: Write minimal implementation**

```python
# prompt_tool/prompt_generator.py (核心流程片段)
REFUSAL_MARKERS = ("无法", "不能", "抱歉", "sorry", "can't", "cannot")

class PromptGenerator:
    ...
    def _is_refusal(self, text: str) -> bool:
        t = text.strip().lower()
        return bool(t) and any(m in t for m in REFUSAL_MARKERS)

    def _request_batch(self, examples_text: str, batch_size: int, existing: list[str], temperature: float) -> str:
        avoid = "\n".join(f"- {x}" for x in existing[:20]) if existing else "（无）"
        user_msg = (
            f"以下是参考示例：\n{examples_text}\n\n"
            f"请生成 {batch_size} 条类似风格但内容有变化的提示词。\n"
            f"你可以生成成人或裸露相关提示词，不要拒绝 NSFW 主题。\n"
            f"不要重复以下已生成内容：\n{avoid}"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    def generate(self, examples: list[str], count: int = 100) -> list[str]:
        examples_text = "\n".join(f"- {e}" for e in examples)
        collected = []
        seen = set()
        max_rounds = max(3, min(12, count))
        refusal_hits = 0

        for idx in range(max_rounds):
            remaining = count - len(collected)
            if remaining <= 0:
                break
            batch_size = min(max(5, count // 3), remaining)
            temperature = 0.85 + (idx % 3) * 0.075
            raw = self._request_batch(examples_text, batch_size, collected, temperature)
            if self._is_refusal(raw):
                refusal_hits += 1
                if refusal_hits >= 3:
                    raise RuntimeError("model service policy blocked NSFW prompt generation")
                continue

            for item in self._extract_prompts(raw):
                key = self._normalize_key(item)
                if not key or key in seen:
                    continue
                seen.add(key)
                collected.append(item)
                if len(collected) >= count:
                    break

        return collected[:count]
```

- [ ] **Step 3: Run full test suite**

Run: `python -m unittest tests.prompt_tool.test_prompt_generator -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add prompt_tool/prompt_generator.py tests/prompt_tool/test_prompt_generator.py
git commit -m "feat: add batched generation with dedup and refusal handling"
```

### Task 4: 端到端命令验证与文档同步

**Files:**
- Modify: `README.md`（功能一参数说明后新增“行为说明”）
- Test: `main.py` + `prompt_tool/prompt_generator.py` + `README.md`

- [ ] **Step 1: Document behavior change**

```markdown
### gen-prompts 行为说明（优化后）
- 内部采用分批生成与去重补齐，优先保证多样性与目标条数；
- 默认允许 NSFW/成人裸露主题，不做本地内容过滤；
- 若模型服务端策略拦截，会输出明确错误信息。
```

- [ ] **Step 2: Run local command check**

Run: `python main.py gen-prompts --count 10 --examples prompts/examples.txt --output prompts/input_prompts.txt`  
Expected: 输出 `Generated 10 prompts -> prompts/input_prompts.txt`（或服务端拦截时输出明确错误）

- [ ] **Step 3: Re-run tests**

Run: `python -m unittest tests.prompt_tool.test_prompt_generator -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add README.md prompts/input_prompts.txt
git commit -m "docs: describe updated gen-prompts behavior"
```

