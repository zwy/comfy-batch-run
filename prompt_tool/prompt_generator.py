from openai import OpenAI
from .prompt_templates import SYSTEM_PROMPT


class PromptGenerator:
    def __init__(self, api_key, base_url=None, model="gpt-4o-mini"):
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model

    def generate(self, examples: list[str], count: int = 100) -> list[str]:
        examples_text = "\n".join(f"- {e}" for e in examples)
        user_msg = f"以下是参考示例：\n{examples_text}\n\n请生成 {count} 条类似风格的提示词。"

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.9,
        )
        raw = resp.choices[0].message.content or ""
        prompts = [line.strip() for line in raw.splitlines() if line.strip()]
        return prompts[:count]
