"""
测试生成相关的API路由
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from core.evaluators.test_generator import IntelligentTestGenerator

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalyzeCodeRequest(BaseModel):
    """代码分析请求"""
    code: str = Field(..., description="要分析的代码")

class AnalyzeCodeResponse(BaseModel):
    """代码分析响应"""
    analysis: Dict[str, Any] = Field(..., description="代码分析结果")

class GenerateTestRequest(BaseModel):
    """测试生成请求"""
    code: str = Field(..., description="要为其生成测试的代码")
    requirement: str = Field(..., description="原始需求描述")
    provider: Optional[str] = Field(None, description="AI提供者名称")
    test_strategy: Optional[str] = Field("intelligent", description="测试策略：intelligent, functional, boundary, performance")

class GenerateTestResponse(BaseModel):
    """测试生成响应"""
    tests_code: str = Field(..., description="生成的测试代码")
    analysis: Dict[str, Any] = Field(..., description="代码分析结果")
    strategy_used: str = Field(..., description="使用的测试策略")

@router.post("/analyze-code", response_model=AnalyzeCodeResponse)
async def analyze_code(request: AnalyzeCodeRequest, req: Request):
    """
    分析代码结构
    
    Args:
        request: 代码分析请求
        req: FastAPI请求对象
        
    Returns:
        代码分析结果
    """
    try:
        provider_manager = req.app.state.provider_manager
        test_generator = IntelligentTestGenerator(provider_manager)
        
        # 分析代码
        analysis = test_generator.analyzer.analyze_code(request.code)
        
        logger.info("✅ 代码分析完成")
        
        return AnalyzeCodeResponse(analysis=analysis)
        
    except Exception as e:
        logger.error(f"❌ 代码分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"代码分析失败: {str(e)}")

@router.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test_for_code(request: GenerateTestRequest, req: Request):
    """
    为指定代码生成测试用例
    
    Args:
        request: 测试生成请求
        req: FastAPI请求对象
        
    Returns:
        生成的测试代码和分析结果
    """
    try:
        provider_manager = req.app.state.provider_manager
        test_generator = IntelligentTestGenerator(provider_manager)
        
        # 先分析代码
        analysis = test_generator.analyzer.analyze_code(request.code)
        
        # 根据策略生成测试
        if request.test_strategy == "intelligent":
            tests_code = await test_generator.generate_tests_for_code(
                code=request.code,
                requirement=request.requirement,
                provider_name=request.provider
            )
            strategy_used = "intelligent"
            
        elif request.test_strategy == "multiple":
            # 生成多种测试策略
            strategies = await test_generator.generate_multiple_test_strategies(
                code=request.code,
                requirement=request.requirement
            )
            
            # 合并所有策略的测试
            all_tests = []
            for strategy in strategies:
                strategy_prompt = strategy["prompt"]
                provider_name = request.provider or provider_manager.get_provider_names()[0]
                provider = provider_manager.get_provider(provider_name)
                
                if provider:
                    strategy_tests = await provider.generate_code(
                        requirement=strategy_prompt,
                        language="python",
                        extra_directives="生成pytest格式的测试代码"
                    )
                    all_tests.append(f"# {strategy['type'].upper()} TESTS\n{strategy_tests}\n")
            
            tests_code = "\n".join(all_tests)
            strategy_used = "multiple"
            
        else:
            # 默认使用智能策略
            tests_code = await test_generator.generate_tests_for_code(
                code=request.code,
                requirement=request.requirement,
                provider_name=request.provider
            )
            strategy_used = request.test_strategy
        
        logger.info(f"✅ 测试生成完成，策略: {strategy_used}")
        
        return GenerateTestResponse(
            tests_code=tests_code,
            analysis=analysis,
            strategy_used=strategy_used
        )
        
    except Exception as e:
        logger.error(f"❌ 测试生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试生成失败: {str(e)}")

@router.get("/test-strategies")
async def get_test_strategies():
    """
    获取可用的测试策略
    
    Returns:
        测试策略列表
    """
    strategies = [
        {
            "name": "intelligent",
            "description": "智能测试策略 - 基于代码结构自动分析生成全面测试",
            "features": ["代码结构分析", "参数类型推断", "复杂度评估", "自动测试分类"]
        },
        {
            "name": "functional", 
            "description": "功能测试策略 - 专注于核心功能正确性验证",
            "features": ["基本功能测试", "返回值验证", "逻辑流程测试"]
        },
        {
            "name": "boundary",
            "description": "边界测试策略 - 专注于边界条件和异常情况",
            "features": ["边界值测试", "异常输入测试", "空值处理测试"]
        },
        {
            "name": "performance",
            "description": "性能测试策略 - 验证算法效率和性能指标",
            "features": ["时间复杂度验证", "大数据集测试", "内存使用测试"]
        },
        {
            "name": "multiple",
            "description": "综合测试策略 - 结合多种策略生成全面测试套件",
            "features": ["多策略结合", "全面覆盖", "分类组织"]
        }
    ]
    
    return {"strategies": strategies}

@router.post("/demo-generate")
async def demo_intelligent_testing(req: Request):
    """
    演示智能测试生成功能
    
    Returns:
        演示结果
    """
    demo_code = '''def solve(n):
    """计算斐波那契数列的第n项"""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for i in range(2, n + 1):
            a, b = b, a + b
        return b
'''
    
    demo_requirement = "实现一个计算斐波那契数列第n项的函数，要求处理边界情况"
    
    try:
        provider_manager = req.app.state.provider_manager
        test_generator = IntelligentTestGenerator(provider_manager)
        
        # 分析演示代码
        analysis = test_generator.analyzer.analyze_code(demo_code)
        
        # 生成智能测试
        tests_code = await test_generator.generate_tests_for_code(
            code=demo_code,
            requirement=demo_requirement
        )
        
        return {
            "demo_code": demo_code,
            "requirement": demo_requirement,
            "analysis": analysis,
            "generated_tests": tests_code,
            "message": "演示完成！智能测试生成器已分析代码结构并生成了针对性的测试用例。"
        }
        
    except Exception as e:
        logger.error(f"❌ 演示失败: {e}")
        raise HTTPException(status_code=500, detail=f"演示失败: {str(e)}")
