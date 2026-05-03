import json
import pathlib
from .comfy_client import ComfyClient


class BatchRunner:
    def __init__(self, config):
        self.client = ComfyClient(config["server"])
        self.workflow_template = json.load(open(config["workflow_template"], "r", encoding="utf-8"))
        self.output_dir = pathlib.Path(config["output_dir"])
        self.output_dir.mkdir(exist_ok=True)

    def inject_prompt(self, workflow: dict, prompt_text: str) -> dict:
        wf = json.loads(json.dumps(workflow))
        for node in wf.values():
            if node.get("class_type") == "CLIPTextEncode":
                title = node.get("_meta", {}).get("title", "").lower()
                if "positive" in title:
                    node["inputs"]["text"] = prompt_text
                    break
        return wf

    def run(self, prompts: list[str]):
        for i, prompt_text in enumerate(prompts):
            print(f"[{i+1}/{len(prompts)}] Queuing: {prompt_text[:60]}...")
            wf = self.inject_prompt(self.workflow_template, prompt_text)
            prompt_id = self.client.queue_prompt(wf)
            history = self.client.wait_for_result(prompt_id)
            for node_output in history.get("outputs", {}).values():
                for img in node_output.get("images", []):
                    ext = img["filename"].split(".")[-1]
                    save_path = self.output_dir / f"{i+1:04d}.{ext}"
                    self.client.download_image(
                        img["filename"], img.get("subfolder", ""), img["type"], save_path
                    )
                    print(f"  Saved: {save_path}")
