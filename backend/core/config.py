"""
配置管理模块
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class Config:
    """全局配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的config.json
        """
        # 加载环境变量
        load_dotenv()
        
        # 确定配置文件路径
        if config_path is None:
            # 从当前文件位置推断项目根目录
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            config_path = project_root / "config.json"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except FileNotFoundError:
            print(f"⚠️  配置文件未找到: {self.config_path}")
            self._config = self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "providers": [],
            "scoring": {
                "weights": {
                    "bleu": 0.35,
                    "tests_pass_rate": 0.45,
                    "ast_quality": 0.2
                }
            },
            "enhanced_evaluation": {
                "enabled": False,
                "weights": {
                    "functionality": 0.35,
                    "quality": 0.25,
                    "style": 0.15,
                    "security": 0.15,
                    "maintainability": 0.10
                }
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": True
            },
            "timeouts": {
                "generation": 60,
                "evaluation": 30,
                "test_execution": 20
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """保存配置到文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    @property
    def providers(self) -> list:
        """获取AI提供者配置"""
        return self.get("providers", [])
    
    @property
    def scoring_weights(self) -> Dict[str, float]:
        """获取评分权重"""
        return self.get("scoring.weights", {})
    
    @property
    def server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self.get("server", {})
    
    @property
    def timeouts(self) -> Dict[str, int]:
        """获取超时配置"""
        return self.get("timeouts", {})
    
    @property
    def roles(self) -> Dict[str, Any]:
        """获取角色配置"""
        return self.get("roles", {})
    
    @property
    def available_roles(self) -> Dict[str, Any]:
        """获取可用角色列表"""
        return self.get("roles.available_roles", {})
    
    @property
    def default_role(self) -> str:
        """获取默认角色"""
        return self.get("roles.default", "developer")
    
    def get_role_config(self, role_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定角色的配置
        
        Args:
            role_id: 角色ID
            
        Returns:
            角色配置，如果不存在返回None
        """
        roles = self.available_roles
        return roles.get(role_id)
    
    def get_role_prompt_template(self, role_id: str) -> str:
        """
        获取指定角色的提示词模板
        
        Args:
            role_id: 角色ID
            
        Returns:
            提示词模板，如果角色不存在返回默认模板
        """
        role_config = self.get_role_config(role_id)
        if role_config:
            return role_config.get("prompt_template", "")
        
        # 如果角色不存在，返回默认开发人员角色的模板
        default_role_config = self.get_role_config(self.default_role)
        if default_role_config:
            return default_role_config.get("prompt_template", "")
        
        return "请根据需求编写高质量的代码。"

# 全局配置实例
config = Config()
