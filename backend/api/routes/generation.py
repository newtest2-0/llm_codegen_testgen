"""
代码生成相关的API路由
"""
import uuid
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Request
from typing import List
from pydantic import BaseModel

from models import GenerateRequest, GenerateResponse, CodeArtifact
from core.providers import ProviderManager
from core.evaluators.test_generator import IntelligentTestGenerator

logger = logging.getLogger(__name__)
class RefineRequirementRequest(BaseModel):
    """需求优化请求"""
    requirement: str
    language: str = "python"
    extra_directives: str = None
    preferred_refiner: str = None  # 可选：指定用于需求优化的模型

class RefineRequirementResponse(BaseModel):
    """需求优化响应"""
    refined_requirement: str
    original_requirement: str
    refinement_provider: str

router = APIRouter()

@router.post("/refine-requirement", response_model=RefineRequirementResponse)
async def refine_requirement(request: RefineRequirementRequest, req: Request):
    """
    优化需求描述，使其更加专业和详细
    
    Args:
        request: 需求优化请求
        req: FastAPI请求对象
        
    Returns:
        优化后的需求描述
    """
    # 获取提供者管理器
    provider_manager: ProviderManager = req.app.state.provider_manager
    
    # 选择用于需求优化的提供者
    available_providers = provider_manager.get_provider_names()
    
    # 如果用户指定了特定的模型，优先使用
    if request.preferred_refiner and request.preferred_refiner in available_providers:
        refiner_provider = request.preferred_refiner
        logger.info(f"使用用户指定的模型进行需求优化: {refiner_provider}")
    else:
        # 否则按优先级选择（优先选择GPT-4或Claude等高质量模型）
        # 可以调整这个列表来改变优先级顺序
        preferred_providers = ["claude", "deepseek", "openai", "gemini"]  # 例如：Claude优先
        
        # 找到第一个可用的优先提供者
        refiner_provider = None
        for provider in preferred_providers:
            if provider in available_providers:
                refiner_provider = provider
                break
        
        # 如果没有优先提供者，使用第一个可用的
        if not refiner_provider and available_providers:
            refiner_provider = available_providers[0]
    
    if not refiner_provider:
        raise HTTPException(status_code=400, detail="没有可用的AI提供者进行需求优化")
    
    provider = provider_manager.get_provider(refiner_provider)
    
    # 构建需求优化的提示词
    refinement_prompt = f"""作为资深技术专家，请将以下用户需求优化为简洁而专业的技术需求：

原始需求：{request.requirement}
目标语言：{request.language}
额外要求：{request.extra_directives or "无"}

请输出精炼的技术需求，包含：

**核心功能**：明确要实现的主要功能和预期行为

**技术要点**：
- 建议的函数/类名称和核心接口
- 关键参数和返回值类型
- 必要的异常处理策略

**质量标准**：代码规范、测试要求、性能考量

要求：简洁明了、技术专业、易于理解，避免冗长的格式化文档。直接输出优化需求，无需解释。"""

    try:
        logger.info(f"使用 {refiner_provider} 进行需求优化...")
        
        refined_requirement = await provider.generate_code(
            requirement=refinement_prompt,
            language="text",  # 这里是文本生成，不是代码
            extra_directives="输出详细的技术需求文档"
        )
        
        logger.info(f"✅ 需求优化完成")
        
        return RefineRequirementResponse(
            refined_requirement=refined_requirement,
            original_requirement=request.requirement,
            refinement_provider=refiner_provider
        )
        
    except Exception as e:
        logger.error(f"❌ 需求优化失败: {e}")
        raise HTTPException(status_code=500, detail=f"需求优化失败: {str(e)}")

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
