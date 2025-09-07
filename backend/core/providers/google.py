"""
Google Gemini AI提供者
"""
import os
import httpx
import logging
from typing import Dict, Any
from .base import ProviderBase

logger = logging.getLogger(__name__)

class GoogleProvider(ProviderBase):
    """Google Gemini提供者"""
    
    async def generate(self, prompt: str) -> str:
        """
        使用Google Gemini API生成代码
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的代码
        """
        api_key = os.environ.get(self.api_key_env, "")
        
        if not api_key:
            logger.info(f"{self.name}: 未配置API密钥，使用虚拟代码")
            return self._get_demo_code()
        
        async def _make_request():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"You are a senior software engineer. Output ONLY code.\n\n{prompt}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 4096
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
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
    这是一个来自Gemini的演示函数
    请配置GOOGLE_API_KEY以获取真实的AI生成代码
    \"\"\"
    return f'Hello from Gemini ({self.model})!'

if __name__ == '__main__':
    print(solve())
"""
