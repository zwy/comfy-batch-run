import requests
import uuid
import time


class ComfyClient:
    def __init__(self, server="127.0.0.1:8188"):
        self.server = server
        self.client_id = str(uuid.uuid4())

    def queue_prompt(self, workflow: dict) -> str:
        payload = {"prompt": workflow, "client_id": self.client_id}
        resp = requests.post(f"http://{self.server}/prompt", json=payload)
        resp.raise_for_status()
        return resp.json()["prompt_id"]

    def wait_for_result(self, prompt_id: str, poll_interval=2) -> dict:
        while True:
            resp = requests.get(f"http://{self.server}/history/{prompt_id}")
            resp.raise_for_status()
            history = resp.json()
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(poll_interval)

    def download_image(self, filename, subfolder, folder_type, save_path):
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        resp = requests.get(f"http://{self.server}/view", params=params)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(resp.content)
