import json
import os
import re
from typing import List, Optional

import requests
from dotenv import load_dotenv


class GlmAi:
    """Helper around GLM official chat completion API for tagging and classification."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.5-air",
        base_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        timeout: int = 60,
        env_file: Optional[str] = ".env",
    ) -> None:
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        self.api_key = api_key or os.environ.get("GLM_API_KEY")
        if not self.api_key:
            raise ValueError("GLM_API_KEY is required either via parameter or environment variable")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def generate_summary_and_tags(self, text: str) -> dict:
        """Return summary string and tags list derived from input text."""
        prompt = (
            "请根据以下内容生成一个简短摘要，并给出若干标签。"
            "\n要求返回严格 JSON 格式，例如 {\"summary\": \"...\", \"tags\": [\"...\"]}."
            "\n只返回 JSON。"
        )
        content = self._chat([
            {"role": "system", "content": "你是一名擅长内容分析的助手。"},
            {"role": "user", "content": f"内容如下：\n{text}\n{prompt}"},
        ])

        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?|```$", "", content).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            sanitized = content.replace("'", '"')
            try:
                return json.loads(sanitized)
            except json.JSONDecodeError as exc2:
                raise ValueError(f"GLM 输出无法解析为 JSON: {content}") from exc2

    def classify(
        self,
        summary: str,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
    ) -> str:
        """Return a single category name given summary/tags and optional category list."""
        tags_part = f"，标签：{','.join(tags)}" if tags else ""
        category_prompt = (
            f"可选分类列表：{','.join(categories)}。"
            if categories
            else ""
        )
        prompt = (
            f"请结合以上信息{category_prompt}给出最合适的分类名称，"
            "直接输出分类名称，不要附带额外文字。"
        )
        content = self._chat([
            {"role": "system", "content": "你是一名分类助手，只返回一个分类名称。"},
            {"role": "user", "content": f"摘要：{summary}{tags_part}。{prompt}"},
        ])
        return content.strip()

    def _chat(self, messages: List[dict]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
        }
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"GLM 接口请求失败 {response.status_code}: {response.text}"
            ) from exc

        data = response.json() if response.text else {}
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("GLM 返回为空: {}".format(data))
        message = choices[0].get("message", {})
        return message.get("content", "")
