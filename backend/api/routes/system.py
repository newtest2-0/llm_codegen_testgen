"""
系统管理相关的API路由
"""
import logging
from fastapi import APIRouter, Request
from typing import Dict, Any

from core.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status")
async def get_system_status(req: Request) -> Dict[str, Any]:
    """
    获取系统状态
    
    Args:
        req: FastAPI请求对象
        
    Returns:
        系统状态信息
    """
    provider_manager = req.app.state.provider_manager
    
    return {
        "ok": True,
        "version": "2.0.0",
        "providers": {
            "total": len(provider_manager),
            "available": provider_manager.get_provider_names(),
            "status": provider_manager.get_status()
        },
        "features": {
            "enhanced_evaluation": config.get("enhanced_evaluation.enabled", False),
            "supported_languages": ["python", "other"]
        },
        "config": {
            "timeouts": config.timeouts,
            "scoring_weights": config.scoring_weights
        }
    }

@router.get("/providers")
async def list_providers(req: Request) -> Dict[str, Any]:
    """
    获取所有AI提供者信息
    
    Args:
        req: FastAPI请求对象
        
    Returns:
        提供者信息
    """
    provider_manager = req.app.state.provider_manager
    return provider_manager.get_status()

@router.post("/providers/reload")
async def reload_providers(req: Request) -> Dict[str, str]:
    """
    重新加载提供者配置
    
    Args:
        req: FastAPI请求对象
        
    Returns:
        操作结果
    """
    provider_manager = req.app.state.provider_manager
    provider_manager.reload_providers()
    
    return {
        "message": "提供者配置已重新加载",
        "providers": provider_manager.get_provider_names()
    }
