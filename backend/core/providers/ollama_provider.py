"""
Ollama本地模型提供者
"""
import asyncio
import logging
import requests
from typing import Dict, Any

from .base import ProviderBase

logger = logging.getLogger(__name__)


class OllamaProvider(ProviderBase):
    """Ollama本地模型提供者，通过 /api/chat 接口调用本地运行的模型"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")

    async def generate(self, prompt: str) -> str:
        """
        调用Ollama Chat API生成代码

        Args:
            prompt: 提示词

        Returns:
            生成的代码字符串
        """
        async def _call():
            return self._sync_chat(prompt)

        return await self._retry_request(_call)

    def _sync_chat(self, prompt: str) -> str:
        """同步调用Ollama /api/chat，在线程池中执行以避免阻塞事件循环"""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        content = response.json()["message"]["content"]
        return self._clean_code_response(content)
