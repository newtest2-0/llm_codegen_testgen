"""
集成RAG的代码生成模块

在原有代码生成基础上，添加RAG知识检索增强功能
"""
from fastapi import Request
from typing import Optional
import logging

from core.rag import KnowledgeBase, KnowledgeRetriever, TextEmbedder
from core.providers import ProviderManager

logger = logging.getLogger(__name__)

# 初始化RAG组件
knowledge_base = KnowledgeBase("data/knowledge_base.json")
embedder = TextEmbedder()
retriever = KnowledgeRetriever(knowledge_base, embedder)


async def generate_with_rag(
    requirement: str,
    language: str,
    provider_manager: ProviderManager,
    provider_name: str,
    extra_directives: Optional[str] = None,
    use_rag: bool = True,
    auto_save: bool = True
) -> tuple[str, Optional[list]]:
    """
    使用RAG增强的代码生成
    
    Args:
        requirement: 需求描述
        language: 编程语言
        provider_manager: 提供者管理器
        provider_name: 提供者名称
        extra_directives: 额外指令
        use_rag: 是否使用RAG增强
        auto_save: 是否自动保存高质量代码
    
    Returns:
        (生成的代码, 参考案例列表)
    """
    provider = provider_manager.get_provider(provider_name)
    references = None
    
    if use_rag:
        # 检索相似案例
        results = retriever.retrieve(
            query=requirement,
            top_k=3,
            language=language,
            min_quality=0.6
        )
        
        if results:
            logger.info(f"[RAG] 找到 {len(results)} 个相似案例")
            references = [
                {
                    "id": r.entry.id,
                    "requirement": r.entry.requirement,
                    "code": r.entry.code,
                    "similarity": r.score,
                    "quality": r.entry.quality_score,
                    "tags": r.entry.tags
                }
                for r in results
            ]
            
            # 使用增强的prompt
            enhanced_prompt = retriever.build_enhanced_prompt(
                requirement=requirement,
                language=language,
                top_k=3
            )
            
            code = await provider.generate_code(
                requirement=enhanced_prompt,
                language=language,
                extra_directives=extra_directives
            )
            
            logger.info("[RAG] 使用增强prompt生成代码")
        else:
            logger.info("[RAG] 未找到相似案例，使用标准prompt")
            code = await provider.generate_code(
                requirement=requirement,
                language=language,
                extra_directives=extra_directives
            )
    else:
        # 不使用RAG，标准生成
        code = await provider.generate_code(
            requirement=requirement,
            language=language,
            extra_directives=extra_directives
        )
    
    return code, references


async def auto_save_to_knowledge_base(
    requirement: str,
    code: str,
    language: str,
    quality_score: float,
    test_results: Optional[dict] = None
) -> Optional[str]:
    """
    自动保存高质量代码到知识库
    
    Args:
        requirement: 需求描述
        code: 生成的代码
        language: 编程语言
        quality_score: 质量分数
        test_results: 测试结果
    
    Returns:
        保存的条目ID，如果未保存则返回None
    """
    # 质量阈值
    QUALITY_THRESHOLD = 0.80
    
    if quality_score < QUALITY_THRESHOLD:
        logger.info(f"[RAG] 质量分数 {quality_score:.2f} 未达到阈值，不自动保存")
        return None
    
    # 建议标签
    tags = retriever.suggest_tags(requirement)
    
    # 添加到知识库
    try:
        entry_id = knowledge_base.add_entry(
            requirement=requirement,
            code=code,
            language=language,
            tags=tags,
            quality_score=quality_score,
            test_results=test_results,
            metadata={"auto_saved": True}
        )
        
        # 清空缓存
        retriever.clear_cache()
        
        logger.info(f"[RAG] 高质量代码已自动保存: {entry_id}")
        return entry_id
        
    except Exception as e:
        logger.error(f"[ERROR] 自动保存失败: {e}")
        return None


def get_knowledge_statistics() -> dict:
    """获取知识库统计信息"""
    return knowledge_base.get_statistics()


def get_retriever_instance():
    """获取检索器实例"""
    return retriever


def get_knowledge_base_instance():
    """获取知识库实例"""
    return knowledge_base

