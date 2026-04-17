"""
AI提供者模块
"""
from .base import ProviderBase
from .openai_compatible import OpenAICompatibleProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .ollama_provider import OllamaProvider
from .manager import ProviderManager

PROVIDERS = {
    "openai_compatible": OpenAICompatibleProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "ollama": OllamaProvider,
}

__all__ = [
    "ProviderBase",
    "OpenAICompatibleProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "OllamaProvider",
    "ProviderManager",
    "PROVIDERS",
]
