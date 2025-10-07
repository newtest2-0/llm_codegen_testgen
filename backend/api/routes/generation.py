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
from core.api_key_storage import api_key_storage
from .system import metrics

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
        # 否则选择有API密钥的优质提供者
        refiner_provider = _select_best_test_provider(provider_manager, available_providers)
    
    if not refiner_provider:
        raise HTTPException(status_code=400, detail="没有可用的AI提供者进行需求优化")
    
    provider = provider_manager.get_provider(refiner_provider)
    
    # 构建需求优化的提示词
    refinement_prompt = f"""请将用户的需求描述优化为更加具体和明确的需求说明：

原始需求：{request.requirement}
目标语言：{request.language}
额外要求：{request.extra_directives or "无"}

请优化为具体的功能需求描述，要求：
1. 明确要实现什么功能
2. 说明具体的输入输出要求
3. 描述关键的业务逻辑
4. 指出需要注意的边界条件

输出简洁的功能需求描述，用自然语言表达，不需要技术框架或格式化文档。"""

    try:
        logger.info(f"使用 {refiner_provider} 进行需求优化...")
        
        refined_requirement = await provider.generate_code(
            requirement=refinement_prompt,
            language="text",  # 这里是文本生成，不是代码
            extra_directives="输出简洁明确的功能需求描述，避免复杂的技术文档格式"
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
    # 开始请求跟踪
    start_time = metrics.start_request()
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
            
            # 构建包含角色提示词的完整需求
            enhanced_requirement = request.requirement
            if request.role_prompt:
                enhanced_requirement = f"{request.role_prompt}\n\n需求描述：\n{request.requirement}"
                logger.info(f"使用角色 '{request.role}' 的提示词增强需求")
            
            code = await provider.generate_code(
                requirement=enhanced_requirement,
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
        # 选择有可用API密钥的提供者进行测试生成
        test_provider_name = request.test_generator_provider or _select_best_test_provider(provider_manager, provider_names)
        
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
                provider_name=test_provider_name,
                role=request.role,
                role_prompt=request.role_prompt
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
                    logger.info("✅ 基础测试用例生成完成")
                except Exception as e2:
                    logger.error(f"❌ 基础测试生成也失败: {e2}")
                    # 最终回退到静态测试模板
                    tests_code = f"""# 测试用例生成失败，使用基础模板
import pytest

def test_basic_functionality():
    \"\"\"基础功能测试
    
    原始需求：{request.requirement}
    \"\"\"
    # TODO: 请根据实际生成的代码实现具体测试逻辑
    # 这是一个占位符测试，确保测试框架可以运行
    assert True, "请实现具体的测试逻辑"

def test_edge_cases():
    \"\"\"边界情况测试\"\"\"
    # TODO: 添加边界条件测试
    assert True, "请添加边界条件测试"

def test_error_handling():
    \"\"\"异常处理测试\"\"\"
    # TODO: 添加异常处理测试
    assert True, "请添加异常处理测试"
"""
            else:
                logger.error(f"❌ 测试提供者 {test_provider_name} 不可用")
                tests_code = f"""# 测试提供者不可用，使用静态模板
import pytest

def test_placeholder():
    \"\"\"占位符测试 - 需要手动实现
    
    原始需求：{request.requirement}
    \"\"\"
    # 由于AI提供者不可用，请手动实现测试逻辑
    assert True, "请根据生成的代码手动实现测试"
"""
    
    logger.info(f"会话 {session_id} 代码生成完成，共生成 {len(artifacts)} 个方案")
    
    # 结束请求跟踪
    response_time = metrics.end_request(start_time)
    logger.info(f"请求处理时间: {response_time:.2f}ms")
    
    return GenerateResponse(
        session_id=session_id,
        artifacts=artifacts,
        tests_code=tests_code,
        language=request.language,
        test_provider=test_provider_name if request.language == "python" else None
    )

def _select_best_test_provider(provider_manager: ProviderManager, provider_names: List[str]) -> str:
    """
    选择最佳的测试生成提供者
    优先选择有可用API密钥的提供者
    
    Args:
        provider_manager: 提供者管理器
        provider_names: 可用提供者名称列表
        
    Returns:
        选中的提供者名称
    """
    # 检查每个提供者的API密钥可用性
    providers_with_keys = []
    providers_without_keys = []
    
    for provider_name in provider_names:
        api_key = api_key_storage.get_api_key(provider_name)
        if api_key and api_key.strip():
            providers_with_keys.append(provider_name)
            logger.info(f"提供者 {provider_name} 有可用的API密钥")
        else:
            providers_without_keys.append(provider_name)
            logger.info(f"提供者 {provider_name} 没有API密钥")
    
    # 优先选择有API密钥的提供者
    if providers_with_keys:
        # 按优先级排序（可以根据需要调整优先级）
        priority_order = ["claude", "deepseek", "openai", "gemini", "qwen", "baichuan", "chatglm"]
        
        for preferred in priority_order:
            if preferred in providers_with_keys:
                logger.info(f"选择提供者 {preferred} 进行测试生成（有API密钥，优先级高）")
                return preferred
        
        # 如果没有优先级匹配，选择第一个有密钥的
        selected = providers_with_keys[0]
        logger.info(f"选择提供者 {selected} 进行测试生成（有API密钥）")
        return selected
    
    # 如果都没有API密钥，选择第一个（会使用虚拟代码）
    if provider_names:
        selected = provider_names[0]
        logger.warning(f"所有提供者都没有API密钥，选择 {selected}（将使用虚拟代码）")
        return selected
    
    # 如果没有可用提供者，抛出异常
    raise ValueError("没有可用的提供者进行测试生成")
