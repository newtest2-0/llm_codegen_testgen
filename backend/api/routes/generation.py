"""
代码生成相关的API路由
"""
import uuid
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Request
from typing import List

from models import GenerateRequest, GenerateResponse, CodeArtifact
from core.providers import ProviderManager
from core.evaluators.test_generator import IntelligentTestGenerator

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest, req: Request):
    """
    生成代码
    
    Args:
        request: 代码生成请求
        req: FastAPI请求对象
        
    Returns:
        代码生成响应
    """
    # 获取提供者管理器
    provider_manager: ProviderManager = req.app.state.provider_manager
    
    # 确定要使用的提供者
    provider_names = request.providers or provider_manager.get_provider_names()
    
    # 验证提供者
    try:
        provider_manager.validate_providers(provider_names)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not provider_names:
        raise HTTPException(status_code=400, detail="没有可用的AI提供者")
    
    session_id = uuid.uuid4().hex[:8]
    logger.info(f"开始代码生成会话: {session_id}")
    
    # 并行生成代码
    async def generate_from_provider(provider_name: str) -> CodeArtifact:
        """从单个提供者生成代码"""
        provider = provider_manager.get_provider(provider_name)
        try:
            logger.info(f"使用 {provider_name} 生成代码...")
            code = await provider.generate_code(
                requirement=request.requirement,
                language=request.language,
                extra_directives=request.extra_directives
            )
            logger.info(f"✅ {provider_name} 代码生成完成")
            return CodeArtifact(
                provider=provider_name,
                model=provider.model,
                code=code
            )
        except Exception as e:
            logger.error(f"❌ {provider_name} 代码生成失败: {e}")
            # 返回错误代码而不是抛出异常
            return CodeArtifact(
                provider=provider_name,
                model=provider.model,
                code=f"# 代码生成失败: {str(e)}\ndef solve():\n    return 'generation_failed'"
            )
    
    # 并行执行所有提供者
    tasks = [generate_from_provider(name) for name in provider_names]
    artifacts = await asyncio.gather(*tasks)
    
    # 智能生成测试代码（如果是Python）
    tests_code = None
    if request.language == "python" and artifacts:
        test_provider_name = request.test_generator_provider or provider_names[0]
        
        try:
            logger.info("🧪 启动智能测试用例生成...")
            
            # 初始化智能测试生成器
            test_generator = IntelligentTestGenerator(provider_manager)
            
            # 选择最佳代码作为测试基础（这里选择第一个，实际可以选择评分最高的）
            best_code = artifacts[0].code if artifacts else ""
            
            # 基于实际代码生成智能测试用例
            tests_code = await test_generator.generate_tests_for_code(
                code=best_code,
                requirement=request.requirement,
                provider_name=test_provider_name
            )
            
            logger.info("✅ 智能测试用例生成完成")
            
        except Exception as e:
            logger.error(f"❌ 智能测试生成失败，使用基础测试: {e}")
            # 如果智能生成失败，回退到基础方法
            test_provider = provider_manager.get_provider(test_provider_name)
            if test_provider:
                try:
                    test_prompt = f"""为以下需求生成完整的pytest测试用例：
{request.requirement}

请生成全面的测试用例，包括边界条件和异常情况。
输出纯Python代码，不要包含markdown标记。"""
                    
                    tests_code = await test_provider.generate_code(
                        requirement=test_prompt,
                        language="python",
                        extra_directives="生成pytest格式的测试代码"
                    )
                except Exception as e2:
                    logger.error(f"❌ 基础测试生成也失败: {e2}")
                    tests_code = f"""# 测试代码生成失败: {str(e2)}
import pytest

def test_basic():
    \"\"\"基础测试占位符\"\"\"
    # TODO: 请根据生成的代码手动实现测试
    assert True
"""
    
    logger.info(f"会话 {session_id} 代码生成完成，共生成 {len(artifacts)} 个方案")
    
    return GenerateResponse(
        session_id=session_id,
        artifacts=artifacts,
        tests_code=tests_code,
        language=request.language
    )
