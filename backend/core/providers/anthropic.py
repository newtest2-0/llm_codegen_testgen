"""
Anthropic Claude AI提供者
"""
import os
import httpx
import logging
from typing import Dict, Any
from .base import ProviderBase
from ..api_key_storage import api_key_storage

logger = logging.getLogger(__name__)

class AnthropicProvider(ProviderBase):
    """Anthropic Claude提供者"""

    async def generate(self, prompt: str) -> str:
        """
        使用Anthropic API生成代码

        Args:
            prompt: 提示词

        Returns:
            生成的代码
        """
        api_key = api_key_storage.get_api_key(self.name) or os.environ.get(self.api_key_env, "")
        
        if not api_key:
            logger.info(f"{self.name}: 未配置API密钥，使用虚拟代码")
            return self._get_demo_code()
        
        async def _make_request():
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            payload = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user", 
                        "content": f"You are a senior software engineer. Output ONLY code.\n\n{prompt}"
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"]
                return self._clean_code_response(content)
        
        return await self._retry_request(_make_request)
    
    def _get_demo_code(self) -> str:
        """
        获取演示代码（当API密钥未配置时）
        
        Returns:
            演示代码
        """
        return f"""# 演示代码来自 {self.name} ({self.model})
def solve():
    \"\"\"
    这是一个来自Claude的演示函数
    请配置ANTHROPIC_API_KEY以获取真实的AI生成代码
    \"\"\"
    return f'Hello from Claude ({self.model})!'

if __name__ == '__main__':
    print(solve())
"""
