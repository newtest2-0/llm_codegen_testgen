"""
系统管理相关的API路由
"""
import logging
import time
import asyncio
from fastapi import APIRouter, Request
from typing import Dict, Any
from pydantic import BaseModel

from core.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

# 全局状态跟踪
class SystemMetrics:
    def __init__(self):
        self.active_requests = 0
        self.total_requests = 0
        self.last_request_time = None
        self.average_response_time = 0
        self.response_times = []
        self.max_response_times = 50  # 保留最近50次请求的响应时间
    
    def start_request(self):
        self.active_requests += 1
        self.total_requests += 1
        return time.time()
    
    def end_request(self, start_time: float):
        self.active_requests = max(0, self.active_requests - 1)
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        self.response_times.append(response_time)
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)
        
        # 计算平均响应时间
        if self.response_times:
            self.average_response_time = sum(self.response_times) / len(self.response_times)
        
        self.last_request_time = time.time()
        return response_time

# 全局指标实例
metrics = SystemMetrics()

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

@router.get("/metrics")
async def get_system_metrics(req: Request) -> Dict[str, Any]:
    """
    获取系统实时指标
    
    Args:
        req: FastAPI请求对象
        
    Returns:
        系统实时指标
    """
    provider_manager = req.app.state.provider_manager
    
    # 测试API延迟
    start_time = time.time()
    try:
        # 简单的健康检查来测量延迟
        await asyncio.sleep(0.001)  # 模拟最小处理时间
        api_latency = (time.time() - start_time) * 1000
    except Exception:
        api_latency = -1
    
    return {
        "timestamp": time.time(),
        "api_latency": round(api_latency, 2),
        "average_response_time": round(metrics.average_response_time, 2),
        "active_requests": metrics.active_requests,
        "total_requests": metrics.total_requests,
        "queue_size": metrics.active_requests,  # 当前活跃请求数作为队列大小
        "providers": {
            "total": len(provider_manager),
            "available": len(provider_manager.get_provider_names()),
            "names": provider_manager.get_provider_names()
        },
        "system": {
            "uptime": time.time() - (metrics.last_request_time or time.time()),
            "status": "online" if len(provider_manager.get_provider_names()) > 0 else "offline"
        }
    }

@router.get("/ping")
async def ping_api() -> Dict[str, Any]:
    """
    简单的ping端点用于测量延迟
    
    Returns:
        ping响应
    """
    start_time = time.time()
    response_time = (time.time() - start_time) * 1000
    
    return {
        "pong": True,
        "timestamp": time.time(),
        "response_time": round(response_time, 2)
    }
