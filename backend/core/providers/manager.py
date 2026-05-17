"""
AI提供者管理器
"""
import logging
from typing import Dict, List, Optional, Any
from .base import ProviderBase
from .openai_compatible import OpenAICompatibleProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class ProviderManager:
    """AI提供者管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化提供者管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self._providers: Dict[str, ProviderBase] = {}
        self._load_providers()
    
    def _load_providers(self) -> None:
        """加载配置的提供者"""
        provider_configs = self.config.get("providers", [])
        
        for provider_config in provider_configs:
            try:
                provider = self._create_provider(provider_config)
                self._providers[provider.name] = provider
                logger.info(f"已加载提供者: {provider.name} ({provider.model})")
            except Exception as e:
                logger.error(f"加载提供者失败: {provider_config.get('name', 'unknown')} - {e}")
    
    def _create_provider(self, config: Dict[str, Any]) -> ProviderBase:
        """
        根据配置创建提供者实例
        
        Args:
            config: 提供者配置
            
        Returns:
            提供者实例
            
        Raises:
            ValueError: 不支持的提供者类型
        """
        kind = config.get("kind", "")
        print(f"[DEBUG] Creating provider with config: {config}")
        print(f"[DEBUG] Provider kind: {kind}")
        if kind == "openai_compatible":
            return OpenAICompatibleProvider(config)
        elif kind == "anthropic":
            return AnthropicProvider(config)
        elif kind == "google":
            return GoogleProvider(config)
        elif kind == "ollama":
            return OllamaProvider(config)
        else:
            raise ValueError(f"不支持的提供者类型: {kind}")
    
    def get_provider(self, name: str) -> Optional[ProviderBase]:
        """
        获取指定名称的提供者
        
        Args:
            name: 提供者名称
            
        Returns:
            提供者实例，如果不存在返回None
        """
        return self._providers.get(name)
    
    def get_all_providers(self) -> Dict[str, ProviderBase]:
        """
        获取所有提供者
        
        Returns:
            提供者字典
        """
        return self._providers.copy()
    
    def get_provider_names(self) -> List[str]:
        """
        获取所有提供者名称
        
        Returns:
            提供者名称列表
        """
        return list(self._providers.keys())
    
    def is_provider_available(self, name: str) -> bool:
        """
        检查提供者是否可用
        
        Args:
            name: 提供者名称
            
        Returns:
            是否可用
        """
        return name in self._providers
    
    def validate_providers(self, provider_names: List[str]) -> List[str]:
        """
        验证提供者名称列表
        
        Args:
            provider_names: 提供者名称列表
            
        Returns:
            有效的提供者名称列表
            
        Raises:
            ValueError: 包含无效的提供者名称
        """
        invalid_providers = [name for name in provider_names 
                           if not self.is_provider_available(name)]
        
        if invalid_providers:
            raise ValueError(f"无效的提供者: {', '.join(invalid_providers)}")
        
        return provider_names
    
    def reload_providers(self) -> None:
        """重新加载提供者配置"""
        self._providers.clear()
        self._load_providers()
        logger.info("提供者配置已重新加载")
    
    def add_provider(self, config: Dict[str, Any]) -> None:
        """
        添加新的提供者
        
        Args:
            config: 提供者配置
        """
        provider = self._create_provider(config)
        self._providers[provider.name] = provider
        logger.info(f"已添加提供者: {provider.name}")
    
    def remove_provider(self, name: str) -> None:
        """
        移除提供者
        
        Args:
            name: 提供者名称
        """
        if name in self._providers:
            del self._providers[name]
            logger.info(f"已移除提供者: {name}")
        else:
            logger.warning(f"尝试移除不存在的提供者: {name}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取提供者状态信息
        
        Returns:
            状态信息字典
        """
        return {
            "total_providers": len(self._providers),
            "provider_names": self.get_provider_names(),
            "providers": {
                name: {
                    "name": provider.name,
                    "kind": provider.kind,
                    "model": provider.model
                }
                for name, provider in self._providers.items()
            }
        }
    
    def __len__(self) -> int:
        return len(self._providers)
    
    def __contains__(self, name: str) -> bool:
        return name in self._providers
    
    def __iter__(self):
        return iter(self._providers.values())
    
    def __str__(self) -> str:
        return f"ProviderManager({len(self._providers)} providers)"
    
    def __repr__(self) -> str:
        return f"<ProviderManager: {self.get_provider_names()}>"
