"""
请求模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class GenerateRequest(BaseModel):
    """代码生成请求模型"""
    requirement: str = Field(..., description="需求描述")
    providers: Optional[List[str]] = Field(None, description="AI提供者列表")
    language: str = Field("python", description="编程语言")
    test_generator_provider: Optional[str] = Field(None, description="测试生成器提供者")
    extra_directives: Optional[str] = Field(None, description="额外指令")
    role: Optional[str] = Field("developer", description="开发角色")
    role_prompt: Optional[str] = Field(None, description="角色提示词模板")

class EvaluateRequest(BaseModel):
    """代码评估请求模型"""
    session_id: str = Field(..., description="会话ID")
    artifacts: List["CodeArtifact"] = Field(..., description="代码制品列表")
    tests_code: str = Field(..., description="测试代码")
    language: str = Field("python", description="编程语言")
    requirement: Optional[str] = Field(None, description="原始需求描述，用于增强评估")

# 避免循环导入
from .artifacts import CodeArtifact
EvaluateRequest.model_rebuild()
