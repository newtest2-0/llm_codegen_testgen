"""
设置相关的API路由
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

from core.api_key_storage import api_key_storage

logger = logging.getLogger(__name__)
router = APIRouter()

class SetAPIKeyRequest(BaseModel):
    """设置API密钥请求"""
    provider: str
    api_key: str

class SetAPIKeyResponse(BaseModel):
    """设置API密钥响应"""
    success: bool
    message: str

class GetAPIKeyStatusResponse(BaseModel):
    """获取API密钥状态响应"""
    status: Dict[str, bool]

@router.post("/api-key", response_model=SetAPIKeyResponse)
async def set_api_key(request: SetAPIKeyRequest):
    """
    设置API密钥
    
    Args:
        request: API密钥设置请求
        
    Returns:
        设置结果
    """
    try:
        api_key_storage.set_api_key(request.provider, request.api_key)
        
        if request.api_key.strip():
            message = f"{request.provider.upper()} API密钥已保存"
        else:
            message = f"{request.provider.upper()} API密钥已清除"
        
        logger.info(f"API密钥设置: {request.provider} - {message}")
        
        return SetAPIKeyResponse(
            success=True,
            message=message
        )
        
    except Exception as e:
        logger.error(f"设置API密钥失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")

@router.get("/api-key-status", response_model=GetAPIKeyStatusResponse)
async def get_api_key_status():
    """
    获取所有提供者的API密钥状态
    
    Returns:
        API密钥状态
    """
    try:
        status = api_key_storage.get_all_providers_status()
        return GetAPIKeyStatusResponse(status=status)
        
    except Exception as e:
        logger.error(f"获取API密钥状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.delete("/api-key/{provider}")
async def clear_api_key(provider: str):
    """
    清除指定提供者的API密钥
    
    Args:
        provider: 提供者名称
        
    Returns:
        清除结果
    """
    try:
        api_key_storage.clear_api_key(provider)
        
        return SetAPIKeyResponse(
            success=True,
            message=f"{provider.upper()} API密钥已清除"
        )
        
    except Exception as e:
        logger.error(f"清除API密钥失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除失败: {str(e)}")
