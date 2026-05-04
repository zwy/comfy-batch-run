import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    from prompt_tool.prompt_generator import PromptGenerator
except ModuleNotFoundError as exc:
    if exc.name != "prompt_tool":
        raise
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from prompt_tool.prompt_generator import PromptGenerator


def make_response(text: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


class FakeCompletions:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = self.outputs[min(len(self.calls) - 1, len(self.outputs) - 1)]
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
        call = gen.client.chat.completions.calls[0]
        self.assertEqual(call["model"], "mock-model")
        self.assertIn("messages", call)
        self.assertEqual(call["temperature"], 0.9)

    def test_should_retry_batches_until_count_met(self):
        gen = self.build_gen([
            "portrait woman\nportrait woman",
            "cyberpunk skyline\nmacro flower",
        ])
        result = gen.generate(["portrait style"], count=3)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["portrait woman", "cyberpunk skyline", "macro flower"])
        self.assertEqual(len(gen.client.chat.completions.calls), 2)
        for call in gen.client.chat.completions.calls:
            self.assertEqual(call["model"], "mock-model")
            self.assertIn("messages", call)
            self.assertEqual(call["temperature"], 0.9)

    def test_should_raise_on_repeated_refusal(self):
        gen = self.build_gen([
            "抱歉，我无法生成成人内容",
            "无法协助处理裸露内容",
            "我不能提供该内容",
        ])
        with self.assertRaisesRegex(RuntimeError, "policy|refus|blocked|cannot|disallow|unsafe"):
            gen.generate(["nsfw fashion"], count=2)


if __name__ == "__main__":
    unittest.main()
