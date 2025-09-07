"""
AI提供者基类
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProviderBase(ABC):
    """AI提供者基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化提供者
        
        Args:
            config: 提供者配置
        """
        self.name = config["name"]
        self.kind = config["kind"]
        self.model = config["model"]
        self.base_url_env = config.get("base_url_env", "OPENAI_BASE_URL")
        self.api_key_env = config.get("api_key_env", "OPENAI_API_KEY")
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 60)
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        生成代码
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的代码
        """
        pass
    
    async def generate_code(self, requirement: str, language: str = "python", 
                          extra_directives: Optional[str] = None) -> str:
        """
        生成代码的便捷方法
        
        Args:
            requirement: 需求描述
            language: 编程语言
            extra_directives: 额外指令
            
        Returns:
            生成的代码
        """
        prompt = self._build_code_prompt(requirement, language, extra_directives)
        return await self.generate(prompt)
    
    def _build_code_prompt(self, requirement: str, language: str, 
                          extra_directives: Optional[str] = None) -> str:
        """
        构建代码生成提示词
        
        Args:
            requirement: 需求描述
            language: 编程语言
            extra_directives: 额外指令
            
        Returns:
            提示词
        """
        prompt = f"""Write a single self-contained {language} module that solves the requirement below.
Expose a function `solve()` as the main entry. Avoid network/IO.

Requirement:
{requirement}"""
        
        if extra_directives:
            prompt += f"\n\nExtra directives:\n{extra_directives}"
        
        return prompt
    
    async def _retry_request(self, func, max_retries: Optional[int] = None, 
                           delay: float = 1.0):
        """
        通用重试机制
        
        Args:
            func: 要重试的函数
            max_retries: 最大重试次数
            delay: 初始延迟时间
            
        Returns:
            函数执行结果
        """
        if max_retries is None:
            max_retries = self.max_retries
            
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                logger.warning(
                    f"{self.name} API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                )
                if attempt == max_retries - 1:
                    # 最后一次尝试失败，返回虚拟代码
                    logger.error(f"{self.name} API调用最终失败，使用虚拟代码")
                    return self._get_fallback_code()
                await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
    
    def _get_fallback_code(self) -> str:
        """
        获取API调用失败时的备用代码
        
        Returns:
            备用代码
        """
        return f"""# API调用失败，来自 {self.name} ({self.model}) 的虚拟代码
def solve():
    # TODO: 实现你的解决方案
    return 'API调用失败'

if __name__ == '__main__':
    print(solve())
"""
    
    def _clean_code_response(self, response: str) -> str:
        """
        清理代码响应，移除markdown标记等
        
        Args:
            response: 原始响应
            
        Returns:
            清理后的代码
        """
        cleaned = response.strip()
        
        # 移除常见的markdown代码块标记
        for marker in ["```python", "```py", "```"]:
            cleaned = cleaned.removeprefix(marker).removesuffix(marker)
        
        return cleaned.strip()
    
    def __str__(self) -> str:
        return f"{self.name}({self.model})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}({self.model})>"
