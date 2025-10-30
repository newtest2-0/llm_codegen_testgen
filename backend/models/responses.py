"""
响应模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EvalMetrics(BaseModel):
    """评估指标模型"""
    bleu4: float = Field(..., description="BLEU-4分数")
    rouge: Dict[str, float] = Field(..., description="ROUGE分数")
    pass_at_k: Dict[str, float] = Field(..., description="pass@k分数")
    ast_parse_ok: bool = Field(..., description="AST解析是否成功")
    ast_nodes: int = Field(..., description="AST节点数量")
    cyclomatic: float = Field(..., description="圈复杂度")
    tests: Dict[str, Any] = Field(..., description="测试结果")
    aggregate_score: float = Field(..., description="综合得分")
    enhanced_metrics: Optional[Dict[str, Any]] = Field(None, description="增强评估指标")

class EvalResult(BaseModel):
    """单个评估结果模型"""
    provider: str = Field(..., description="AI提供者名称")
    model: str = Field(..., description="模型名称")
    code_path: str = Field(..., description="代码文件路径")
    metrics: EvalMetrics = Field(..., description="评估指标")

class EvaluateResponse(BaseModel):
    """评估响应模型"""
    session_id: str = Field(..., description="会话ID")
    results: List[EvalResult] = Field(..., description="所有评估结果")
    best: EvalResult = Field(..., description="最佳结果")
    tests_path: str = Field(..., description="测试文件路径")
    
class GenerateResponse(BaseModel):
    """代码生成响应模型"""
    session_id: str = Field(..., description="会话ID")
    artifacts: List["CodeArtifact"] = Field(..., description="生成的代码制品")
    tests_code: Optional[str] = Field(None, description="生成的测试代码")
    language: str = Field(..., description="编程语言")
    test_provider: Optional[str] = Field(None, description="用于测试生成的提供者")
    
# 避免循环导入
from .artifacts import CodeArtifact
GenerateResponse.model_rebuild()
