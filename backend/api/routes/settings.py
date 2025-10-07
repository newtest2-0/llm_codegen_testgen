"""
设置相关的API路由
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

from core.api_key_storage import api_key_storage
from core.config import config

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

class RoleInfo(BaseModel):
    """角色信息"""
    id: str
    name: str
    description: str
    icon: str
    color: str
    prompt_template: str

class GetRolesResponse(BaseModel):
    """获取角色列表响应"""
    roles: Dict[str, RoleInfo]
    default_role: str

class SetDefaultRoleRequest(BaseModel):
    """设置默认角色请求"""
    role_id: str

class SetDefaultRoleResponse(BaseModel):
    """设置默认角色响应"""
    success: bool
    message: str

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

@router.get("/roles", response_model=GetRolesResponse)
async def get_roles():
    """
    获取所有可用角色
    
    Returns:
        角色列表和默认角色
    """
    try:
        available_roles = config.available_roles
        default_role = config.default_role
        
        # 转换为响应格式
        roles_dict = {}
        for role_id, role_config in available_roles.items():
            roles_dict[role_id] = RoleInfo(
                id=role_id,
                name=role_config.get("name", role_id),
                description=role_config.get("description", ""),
                icon=role_config.get("icon", "fas fa-user"),
                color=role_config.get("color", "gray"),
                prompt_template=role_config.get("prompt_template", "")
            )
        
        return GetRolesResponse(
            roles=roles_dict,
            default_role=default_role
        )
        
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取角色失败: {str(e)}")

@router.post("/default-role", response_model=SetDefaultRoleResponse)
async def set_default_role(request: SetDefaultRoleRequest):
    """
    设置默认角色
    
    Args:
        request: 设置默认角色请求
        
    Returns:
        设置结果
    """
    try:
        # 验证角色是否存在
        available_roles = config.available_roles
        if request.role_id not in available_roles:
            raise HTTPException(
                status_code=400, 
                detail=f"角色 '{request.role_id}' 不存在"
            )
        
        # 更新配置
        config.set("roles.default", request.role_id)
        config.save()
        
        role_name = available_roles[request.role_id].get("name", request.role_id)
        
        logger.info(f"默认角色已设置为: {request.role_id} ({role_name})")
        
        return SetDefaultRoleResponse(
            success=True,
            message=f"默认角色已设置为: {role_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置默认角色失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")

@router.get("/role/{role_id}/prompt")
async def get_role_prompt(role_id: str):
    """
    获取指定角色的提示词模板
    
    Args:
        role_id: 角色ID
        
    Returns:
        提示词模板
    """
    try:
        prompt_template = config.get_role_prompt_template(role_id)
        role_config = config.get_role_config(role_id)
        
        if not role_config:
            raise HTTPException(
                status_code=404,
                detail=f"角色 '{role_id}' 不存在"
            )
        
        return {
            "role_id": role_id,
            "role_name": role_config.get("name", role_id),
            "prompt_template": prompt_template
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色提示词失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
