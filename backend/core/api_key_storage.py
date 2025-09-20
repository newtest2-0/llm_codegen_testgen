"""
API密钥存储管理
"""
import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class APIKeyStorage:
    """API密钥存储管理器"""
    
    def __init__(self):
        """初始化存储管理器"""
        self._api_keys: Dict[str, str] = {}
        # 确保使用正确的文件路径，支持从项目根目录或backend目录运行
        possible_paths = [
            Path(".api_keys.json"),  # 当前目录
            Path("backend/.api_keys.json"),  # 从项目根目录运行
            Path("../.api_keys.json")  # 从backend目录运行
        ]
        
        self._storage_file = None
        for path in possible_paths:
            if path.exists():
                self._storage_file = path
                break
        
        # 如果都不存在，使用第一个作为默认
        if self._storage_file is None:
            self._storage_file = Path("backend/.api_keys.json")
            
        self._load_from_file()
    
    def _load_from_file(self) -> None:
        """从文件加载API密钥"""
        try:
            if self._storage_file.exists():
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._api_keys = data.get('api_keys', {})
                logger.info(f"已加载 {len(self._api_keys)} 个API密钥配置")
        except Exception as e:
            logger.warning(f"加载API密钥文件失败: {e}")
            self._api_keys = {}
    
    def _save_to_file(self) -> None:
        """保存API密钥到文件"""
        try:
            data = {"api_keys": self._api_keys}
            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("API密钥已保存到文件")
        except Exception as e:
            logger.error(f"保存API密钥失败: {e}")
    
    def set_api_key(self, provider: str, api_key: str) -> None:
        """
        设置API密钥
        
        Args:
            provider: 提供者名称
            api_key: API密钥
        """
        if api_key.strip():
            self._api_keys[f"{provider}Key"] = api_key.strip()
            logger.info(f"已设置 {provider} 的API密钥")
            
            # 为特定提供者设置默认的base URL
            self._ensure_default_base_url(provider)
        else:
            self._api_keys.pop(f"{provider}Key", None)
            logger.info(f"已清除 {provider} 的API密钥")
        
        self._save_to_file()
    
    def _ensure_default_base_url(self, provider: str) -> None:
        """
        确保提供者有默认的base URL
        
        Args:
            provider: 提供者名称
        """
        base_url_key = f"{provider}BaseUrl"
        if base_url_key not in self._api_keys:
            default_urls = {
                "deepseek": "https://api.deepseek.com",
                "openai": "https://api.openai.com/v1",
                "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "baichuan": "https://api.baichuan-ai.com/v1",
                "chatglm": "https://open.bigmodel.cn/api/paas/v4"
            }
            
            if provider in default_urls:
                self._api_keys[base_url_key] = default_urls[provider]
                logger.info(f"已设置 {provider} 的默认base URL: {default_urls[provider]}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        获取API密钥
        
        Args:
            provider: 提供者名称
            
        Returns:
            API密钥，如果不存在则返回None
        """
        # 首先尝试从存储文件中获取
        api_key = self._api_keys.get(f"{provider}Key")
        if api_key:
            return api_key
        
        # 如果存储文件中没有，尝试从环境变量获取
        env_key_name = f"{provider.upper()}_API_KEY"
        env_key = os.environ.get(env_key_name)
        if env_key:
            return env_key
        
        return None
    
    def get_base_url(self, provider: str) -> Optional[str]:
        """
        获取API基础URL
        
        Args:
            provider: 提供者名称
            
        Returns:
            基础URL，如果不存在则返回None
        """
        # 首先尝试从存储文件获取
        base_url_key = f"{provider}BaseUrl"
        if base_url_key in self._api_keys:
            base_url = self._api_keys[base_url_key]
            if base_url and base_url.strip():
                return base_url.strip()
        
        # 然后尝试从环境变量获取
        env_url_name = f"{provider.upper()}_BASE_URL"
        return os.environ.get(env_url_name)
    
    def has_api_key(self, provider: str) -> bool:
        """
        检查是否有API密钥
        
        Args:
            provider: 提供者名称
            
        Returns:
            是否有API密钥
        """
        return self.get_api_key(provider) is not None
    
    def get_all_providers_status(self) -> Dict[str, bool]:
        """
        获取所有提供者的API密钥状态
        
        Returns:
            提供者状态字典
        """
        providers = ["openai", "deepseek", "claude", "gemini", "qwen", "baichuan", "chatglm"]
        return {provider: self.has_api_key(provider) for provider in providers}
    
    def clear_api_key(self, provider: str) -> None:
        """
        清除API密钥
        
        Args:
            provider: 提供者名称
        """
        self.set_api_key(provider, "")

# 全局API密钥存储实例
api_key_storage = APIKeyStorage()
