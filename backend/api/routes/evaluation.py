"""
代码评估相关的API路由
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from models import EvaluateRequest, EvaluateResponse, EvalResult, EvalMetrics
from core.evaluators.code_quality import ComprehensiveCodeEvaluator, CodeQualityMetrics
from core.evaluators.scoring_metrics import AdvancedScoringMetrics
from core.evaluators.test_generator import IntelligentTestGenerator
from core.evaluators.test_executor import TestExecutor

logger = logging.getLogger(__name__)
router = APIRouter()

class QuickEvaluateRequest(BaseModel):
    """快速评估请求"""
    code: str = Field(..., description="要评估的代码")
    requirement: Optional[str] = Field(None, description="原始需求")

class QuickEvaluateResponse(BaseModel):
    """快速评估响应"""
    metrics: Dict[str, Any] = Field(..., description="评估指标")
    overall_score: float = Field(..., description="综合得分")
    recommendations: List[str] = Field(..., description="改进建议")

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_code(request: EvaluateRequest, req: Request):
    """
    评估代码质量
    
    Args:
        request: 代码评估请求
        req: FastAPI请求对象
        
    Returns:
        代码评估响应
    """
    logger.info(f"开始评估会话: {request.session_id}")
    
    try:
        # 初始化综合评估器
        evaluator = ComprehensiveCodeEvaluator()
        
        # 初始化测试生成器和执行器
        provider_manager = req.app.state.provider_manager
        test_generator = IntelligentTestGenerator(provider_manager)
        test_executor = TestExecutor()
        
        results = []
        
        for artifact in request.artifacts:
            logger.info(f"评估 {artifact.provider} 的代码...")
            
            # 使用综合评估器评估代码
            quality_metrics = evaluator.evaluate_code(
                code=artifact.code,
                requirement=getattr(request, 'requirement', None)
            )
            
            # 生成测试代码
            tests_code = await test_generator.generate_tests_for_code(
                code=artifact.code,
                requirement=getattr(request, 'requirement', ""),
                provider_name=artifact.provider
            )
            
            # 执行测试并收集结果
            test_results = test_executor.run_tests(artifact.code, tests_code)
            passed_tests = test_results["passed_tests"]
            total_tests = test_results["total_tests"]
            
            # 初始化高级评分指标计算器
            scoring_metrics = AdvancedScoringMetrics()
            
            # 计算新的评分指标
            reference_codes = [artifact.code]  # 使用当前代码作为参考
            
            advanced_scores = scoring_metrics.evaluate_generated_code(
                generated_code=artifact.code,
                reference_codes=reference_codes,
                passed_tests=passed_tests,
                total_tests=total_tests
            )
            
            # 转换为原有的评估格式
            eval_metrics = EvalMetrics(
                bleu4=advanced_scores['bleu4'],
                rouge=advanced_scores['rouge'],
                pass_at_k=advanced_scores['pass_at_k'],
                ast_parse_ok=quality_metrics.ast_quality_score > 0,
                ast_nodes=quality_metrics.lines_of_code,
                cyclomatic=quality_metrics.cyclomatic_complexity,
                tests={
                    "supported": True,
                    "passed": passed_tests,
                    "failed": total_tests - passed_tests,
                    "exit_code": 0 if passed_tests > 0 else 1
                },
                aggregate_score=quality_metrics.overall_score,
                # 添加详细的质量指标
                enhanced_metrics={
                    "maintainability_index": quality_metrics.maintainability_index,
                    "style_score": quality_metrics.style_score,
                    "security_score": quality_metrics.security_score,
                    "docstring_coverage": quality_metrics.docstring_coverage,
                    "code_smells": quality_metrics.code_smells,
                    "security_issues": [
                        {"line": issue.get("line"), "message": issue.get("message"), "severity": issue.get("severity")}
                        for issue in quality_metrics.security_issues
                    ],
                    "style_violations": [
                        {"line": violation.get("line"), "message": violation.get("message"), "type": violation.get("type")}
                        for violation in quality_metrics.pep8_violations
                    ]
                }
            )
            
            results.append(EvalResult(
                provider=artifact.provider,
                model=artifact.model,
                code_path="",
                metrics=eval_metrics
            ))
            
            logger.info(f"✅ {artifact.provider} 评估完成，综合得分: {quality_metrics.overall_score:.3f}")
        
        # 选择最佳方案
        best = max(results, key=lambda r: r.metrics.aggregate_score)
        
        logger.info(f"会话 {request.session_id} 评估完成")
        
        return EvaluateResponse(
            session_id=request.session_id,
            results=results,
            best=best,
            tests_path=""
        )
        
    except Exception as e:
        logger.error(f"❌ 代码评估失败: {e}")
        raise HTTPException(status_code=500, detail=f"代码评估失败: {str(e)}")

@router.post("/quick-evaluate", response_model=QuickEvaluateResponse)
async def quick_evaluate(request: QuickEvaluateRequest, req: Request):
    """
    快速评估单个代码片段
    
    Args:
        request: 快速评估请求
        req: FastAPI请求对象
        
    Returns:
        快速评估结果
    """
    try:
        logger.info("开始快速代码质量评估...")
        
        # 初始化评估器
        evaluator = ComprehensiveCodeEvaluator()
        
        # 评估代码
        metrics = evaluator.evaluate_code(request.code, request.requirement)
        
        # 生成改进建议
        recommendations = _generate_recommendations(metrics)
        
        # 初始化高级评分指标计算器
        scoring_metrics = AdvancedScoringMetrics()
        
        # 生成并执行测试来获取真实的测试结果
        provider_manager = req.app.state.provider_manager
        test_generator = IntelligentTestGenerator(provider_manager)
        test_executor = TestExecutor()
        
        # 生成测试代码
        tests_code = await test_generator.generate_tests_for_code(
            code=request.code,
            requirement=request.requirement or "",
            provider_name="default"
        )
        
        # 执行测试并收集结果
        test_results = test_executor.run_tests(request.code, tests_code)
        passed_tests = test_results["passed_tests"]
        total_tests = test_results["total_tests"]
        
        # 计算新的评分指标
        reference_codes = [request.code]  # 使用当前代码作为参考
        
        advanced_scores = scoring_metrics.evaluate_generated_code(
            generated_code=request.code,
            reference_codes=reference_codes,
            passed_tests=passed_tests,
            total_tests=total_tests
        )
        
        # 构建响应
        metrics_dict = {
            "overall_score": metrics.overall_score,
            "bleu4": advanced_scores['bleu4'],
            "rouge": advanced_scores['rouge'],
            "pass_at_k": advanced_scores['pass_at_k'],
            "maintainability_index": metrics.maintainability_index,
            "style_score": metrics.style_score,
            "security_score": metrics.security_score,
            "complexity": {
                "cyclomatic_complexity": metrics.cyclomatic_complexity,
                "cognitive_complexity": metrics.cognitive_complexity,
                "nesting_depth": metrics.nesting_depth
            },
            "documentation": {
                "docstring_coverage": metrics.docstring_coverage,
                "comment_ratio": metrics.comment_ratio
            },
            "issues": {
                "syntax_errors": metrics.syntax_errors,
                "security_issues_count": len(metrics.security_issues),
                "style_violations_count": len(metrics.pep8_violations),
                "code_smells_count": len(metrics.code_smells)
            }
        }
        
        logger.info(f"✅ 快速评估完成，综合得分: {metrics.overall_score:.3f}")
        
        return QuickEvaluateResponse(
            metrics=metrics_dict,
            overall_score=metrics.overall_score,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"❌ 快速评估失败: {e}")
        raise HTTPException(status_code=500, detail=f"快速评估失败: {str(e)}")

@router.get("/quality-standards")
async def get_quality_standards():
    """
    获取代码质量标准说明
    
    Returns:
        质量标准详情
    """
    return {
        "standards": {
            "excellent": {
                "score_range": "0.9 - 1.0",
                "description": "优秀的代码质量",
                "criteria": [
                    "语法完全正确",
                    "遵循PEP8规范",
                    "无安全漏洞",
                    "良好的文档覆盖率",
                    "适当的复杂度",
                    "无代码异味"
                ]
            },
            "good": {
                "score_range": "0.7 - 0.9",
                "description": "良好的代码质量",
                "criteria": [
                    "语法正确",
                    "基本遵循代码规范",
                    "少量安全问题",
                    "有基本文档",
                    "复杂度可控"
                ]
            },
            "fair": {
                "score_range": "0.5 - 0.7",
                "description": "一般的代码质量",
                "criteria": [
                    "语法基本正确",
                    "存在风格问题",
                    "有一些安全隐患",
                    "文档不足",
                    "复杂度较高"
                ]
            },
            "poor": {
                "score_range": "0.0 - 0.5",
                "description": "较差的代码质量",
                "criteria": [
                    "可能有语法错误",
                    "严重违反规范",
                    "存在安全漏洞",
                    "缺乏文档",
                    "复杂度过高"
                ]
            }
        },
        "evaluation_criteria": {
            "functionality": {
                "weight": 0.30,
                "description": "代码语法正确性和基本功能"
            },
            "maintainability": {
                "weight": 0.25,
                "description": "代码可维护性指数"
            },
            "style": {
                "weight": 0.15,
                "description": "代码风格和规范遵循程度"
            },
            "security": {
                "weight": 0.15,
                "description": "安全性和潜在漏洞"
            },
            "documentation": {
                "weight": 0.10,
                "description": "文档和注释质量"
            },
            "complexity": {
                "weight": 0.05,
                "description": "代码复杂度控制"
            }
        }
    }

def _generate_recommendations(metrics: CodeQualityMetrics) -> List[str]:
    """生成改进建议"""
    recommendations = []
    
    # 语法问题
    if metrics.syntax_errors:
        recommendations.append("🔴 修复语法错误以确保代码可以正常运行")
    
    # 安全问题
    if metrics.security_issues:
        critical_issues = [i for i in metrics.security_issues if i.get("severity") == "critical"]
        if critical_issues:
            recommendations.append("🔴 立即修复严重安全漏洞")
        else:
            recommendations.append("🟡 修复安全问题以提高代码安全性")
    
    # 代码风格
    if metrics.style_score < 0.7:
        recommendations.append("🟡 改进代码风格，遵循PEP8规范")
    
    # 复杂度
    if metrics.cyclomatic_complexity > 10:
        recommendations.append("🟡 降低圈复杂度，考虑重构复杂的函数")
    
    if metrics.nesting_depth > 4:
        recommendations.append("🟡 减少嵌套深度，提高代码可读性")
    
    # 文档
    if metrics.docstring_coverage < 0.5:
        recommendations.append("🟡 添加文档字符串，提高代码文档覆盖率")
    
    if metrics.comment_ratio < 0.1:
        recommendations.append("🟡 添加适当的注释说明复杂逻辑")
    
    # 代码异味
    if len(metrics.code_smells) > 3:
        recommendations.append("🟡 重构代码以消除代码异味")
    
    # 综合评分建议
    if metrics.overall_score >= 0.9:
        recommendations.append("🟢 代码质量优秀！继续保持")
    elif metrics.overall_score >= 0.7:
        recommendations.append("🟢 代码质量良好，可以考虑进一步优化")
    elif metrics.overall_score >= 0.5:
        recommendations.append("🟡 代码质量一般，建议按照上述建议进行改进")
    else:
        recommendations.append("🔴 代码质量需要大幅改进，建议重新考虑实现方案")
    
    return recommendations
