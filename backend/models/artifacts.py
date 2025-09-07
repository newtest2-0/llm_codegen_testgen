"""
代码制品模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class CodeArtifact(BaseModel):
    """代码制品模型"""
    provider: str = Field(..., description="AI提供者名称")
    model: str = Field(..., description="模型名称")
    code: str = Field(..., description="生成的代码")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            # 可以添加自定义编码器
        }
