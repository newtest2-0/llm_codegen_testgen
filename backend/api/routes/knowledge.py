"""
知识库管理API
"""
from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel
import logging

from core.rag import KnowledgeBase, KnowledgeRetriever, TextEmbedder

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局知识库实例
knowledge_base = KnowledgeBase("data/knowledge_base.json")
embedder = TextEmbedder()
retriever = KnowledgeRetriever(knowledge_base, embedder)


# === 请求模型 ===

class AddKnowledgeRequest(BaseModel):
    """添加知识请求"""
    requirement: str
    code: str
    language: str
    tags: List[str] = []
    quality_score: float = 1.0
    test_results: Optional[dict] = None
    metadata: Optional[dict] = None


class UpdateKnowledgeRequest(BaseModel):
    """更新知识请求"""
    requirement: Optional[str] = None
    code: Optional[str] = None
    tags: Optional[List[str]] = None
    quality_score: Optional[float] = None
    test_results: Optional[dict] = None
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    top_k: int = 5
    language: Optional[str] = None
    tags: Optional[List[str]] = None
    min_quality: float = 0.0


class EnhancedPromptRequest(BaseModel):
    """增强prompt请求"""
    requirement: str
    language: str
    top_k: int = 3


# === API端点 ===

@router.post("/add")
async def add_knowledge(request: AddKnowledgeRequest):
    """
    添加知识条目
    """
    try:
        entry_id = knowledge_base.add_entry(
            requirement=request.requirement,
            code=request.code,
            language=request.language,
            tags=request.tags,
            quality_score=request.quality_score,
            test_results=request.test_results,
            metadata=request.metadata
        )
        
        # 清空检索缓存
        retriever.clear_cache()
        
        return {
            "success": True,
            "entry_id": entry_id,
            "message": "知识条目添加成功"
        }
    except Exception as e:
        logger.error(f"[ERROR] 添加知识失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entry/{entry_id}")
async def get_knowledge(entry_id: str):
    """
    获取知识条目
    """
    entry = knowledge_base.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    
    return {
        "success": True,
        "entry": entry.to_dict()
    }


@router.delete("/entry/{entry_id}")
async def delete_knowledge(entry_id: str):
    """
    删除知识条目
    """
    success = knowledge_base.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    
    # 清空检索缓存
    retriever.clear_cache()
    
    return {
        "success": True,
        "message": "知识条目删除成功"
    }


@router.put("/entry/{entry_id}")
async def update_knowledge(entry_id: str, request: UpdateKnowledgeRequest):
    """
    更新知识条目
    """
    # 过滤None值
    update_data = {
        k: v for k, v in request.dict().items() 
        if v is not None
    }
    
    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供更新数据")
    
    success = knowledge_base.update_entry(entry_id, **update_data)
    if not success:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    
    # 清空检索缓存
    retriever.clear_cache()
    
    return {
        "success": True,
        "message": "知识条目更新成功"
    }


@router.post("/search")
async def search_knowledge(request: SearchRequest):
    """
    搜索知识库
    """
    try:
        results = retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            language=request.language,
            tags=request.tags,
            min_quality=request.min_quality
        )
        
        return {
            "success": True,
            "count": len(results),
            "results": [r.to_dict() for r in results]
        }
    except Exception as e:
        logger.error(f"[ERROR] 搜索知识失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhanced-prompt")
async def get_enhanced_prompt(request: EnhancedPromptRequest):
    """
    获取增强的prompt
    
    基于知识库中的相似案例，生成增强的prompt
    """
    try:
        enhanced_prompt = retriever.build_enhanced_prompt(
            requirement=request.requirement,
            language=request.language,
            top_k=request.top_k
        )
        
        # 获取使用的参考案例
        results = retriever.retrieve(
            query=request.requirement,
            top_k=request.top_k,
            language=request.language,
            min_quality=0.6
        )
        
        return {
            "success": True,
            "enhanced_prompt": enhanced_prompt,
            "reference_count": len(results),
            "references": [
                {
                    "id": r.entry.id,
                    "similarity": r.score,
                    "quality": r.entry.quality_score
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"[ERROR] 生成增强prompt失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """
    获取知识库统计信息
    """
    stats = knowledge_base.get_statistics()
    return {
        "success": True,
        "statistics": stats
    }


@router.get("/list")
async def list_knowledge(
    language: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    列出知识条目
    """
    entries = knowledge_base.entries
    
    # 按语言过滤
    if language:
        entries = [e for e in entries if e.language == language]
    
    # 分页
    total = len(entries)
    entries = entries[offset:offset + limit]
    
    return {
        "success": True,
        "total": total,
        "count": len(entries),
        "entries": [e.to_dict() for e in entries]
    }


@router.post("/suggest-tags")
async def suggest_tags(requirement: str):
    """
    根据需求建议标签
    """
    tags = retriever.suggest_tags(requirement)
    return {
        "success": True,
        "suggested_tags": tags
    }


@router.post("/auto-save")
async def auto_save_knowledge(
    requirement: str,
    code: str,
    language: str,
    quality_score: float,
    test_results: Optional[dict] = None
):
    """
    自动保存高质量代码
    
    当生成的代码质量分数达到阈值时，自动保存到知识库
    """
    # 质量阈值
    QUALITY_THRESHOLD = 0.8
    
    if quality_score < QUALITY_THRESHOLD:
        return {
            "success": False,
            "message": f"质量分数 {quality_score:.2f} 未达到阈值 {QUALITY_THRESHOLD}"
        }
    
    # 建议标签
    tags = retriever.suggest_tags(requirement)
    
    # 添加到知识库
    entry_id = knowledge_base.add_entry(
        requirement=requirement,
        code=code,
        language=language,
        tags=tags,
        quality_score=quality_score,
        test_results=test_results,
        metadata={"auto_saved": True}
    )
    
    retriever.clear_cache()
    
    return {
        "success": True,
        "entry_id": entry_id,
        "message": "高质量代码已自动保存到知识库",
        "suggested_tags": tags
    }


@router.post("/clear")
async def clear_knowledge():
    """
    清空知识库（谨慎使用）
    """
    knowledge_base.clear()
    retriever.clear_cache()
    
    return {
        "success": True,
        "message": "知识库已清空"
    }


# 导出知识库和检索器实例供其他模块使用
def get_knowledge_base():
    """获取知识库实例"""
    return knowledge_base


def get_retriever():
    """获取检索器实例"""
    return retriever

