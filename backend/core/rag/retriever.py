"""
知识检索模块
从知识库中检索相关经验
"""
from typing import List, Dict, Any, Tuple, Optional
import logging

from .knowledge_base import KnowledgeBase, KnowledgeEntry
from .embedder import TextEmbedder, SimpleEmbedder

logger = logging.getLogger(__name__)


class RetrievalResult:
    """检索结果"""
    
    def __init__(self, entry: KnowledgeEntry, score: float):
        self.entry = entry
        self.score = score
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "entry": self.entry.to_dict(),
            "score": self.score
        }


class KnowledgeRetriever:
    """知识检索器"""
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        embedder: Optional[TextEmbedder] = None
    ):
        self.kb = knowledge_base
        self.embedder = embedder or SimpleEmbedder()
        self._cache: Dict[str, List[float]] = {}
        logger.info("[OK] 知识检索器初始化完成")
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入（带缓存）"""
        if text not in self._cache:
            self._cache[text] = self.embedder.embed(text)
        return self._cache[text]
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_quality: float = 0.0
    ) -> List[RetrievalResult]:
        """
        检索相关知识
        
        Args:
            query: 查询文本（需求描述）
            top_k: 返回top K个结果
            language: 过滤语言
            tags: 过滤标签
            min_quality: 最低质量分数
        
        Returns:
            检索结果列表
        """
        # 过滤候选条目
        candidates = self.kb.entries
        
        if language:
            candidates = [e for e in candidates if e.language == language]
        
        if tags:
            candidates = [
                e for e in candidates 
                if any(tag in e.tags for tag in tags)
            ]
        
        if min_quality > 0:
            candidates = [
                e for e in candidates 
                if e.quality_score >= min_quality
            ]
        
        if not candidates:
            logger.info("[Info] 没有符合条件的知识条目")
            return []
        
        # 计算相似度
        query_embedding = self._get_embedding(query)
        results = []
        
        for entry in candidates:
            # 计算需求相似度
            entry_embedding = self._get_embedding(entry.requirement)
            similarity = self.embedder.cosine_similarity(
                query_embedding,
                entry_embedding
            )
            
            # 综合评分：相似度 * 质量分数
            score = similarity * (0.7 + 0.3 * entry.quality_score)
            
            results.append(RetrievalResult(entry, score))
        
        # 排序并返回top K
        results.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"[OK] 检索到 {len(results[:top_k])} 条相关知识")
        return results[:top_k]
    
    def retrieve_similar_code(
        self,
        requirement: str,
        language: str,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        检索相似代码
        
        Returns:
            [(代码, 相似度分数), ...]
        """
        results = self.retrieve(
            query=requirement,
            top_k=top_k,
            language=language,
            min_quality=0.5
        )
        
        return [(r.entry.code, r.score) for r in results]
    
    def build_enhanced_prompt(
        self,
        requirement: str,
        language: str,
        top_k: int = 3
    ) -> str:
        """
        构建增强的prompt
        
        基于检索到的相似案例，生成更好的prompt
        """
        results = self.retrieve(
            query=requirement,
            top_k=top_k,
            language=language,
            min_quality=0.6
        )
        
        if not results:
            # 没有相关案例，返回原始prompt
            return f"""请根据以下需求生成{language}代码：

需求：
{requirement}

请生成完整、高质量的代码实现。
"""
        
        # 构建包含参考案例的prompt
        examples = []
        for i, result in enumerate(results, 1):
            entry = result.entry
            examples.append(f"""
参考案例 {i} (相似度: {result.score:.2f}, 质量: {entry.quality_score:.2f}):

需求：
{entry.requirement}

代码实现：
```{entry.language}
{entry.code}
```
""")
        
        enhanced_prompt = f"""请根据以下需求生成{language}代码。

我已经为你提供了{len(results)}个相似的参考案例，请参考这些案例的设计思路和实现方式：

{''.join(examples)}

当前需求：
{requirement}

请参考上述案例，生成符合需求的高质量代码实现。注意：
1. 借鉴参考案例的优秀设计模式
2. 确保代码质量和可读性
3. 添加必要的注释和文档
4. 实现完整的错误处理
"""
        
        logger.info(f"[OK] 构建增强prompt，包含 {len(results)} 个参考案例")
        return enhanced_prompt
    
    def suggest_tags(self, requirement: str) -> List[str]:
        """根据需求建议标签"""
        # 常见编程标签
        common_tags = {
            "api": ["api", "接口", "请求", "http", "rest"],
            "database": ["数据库", "sql", "查询", "存储"],
            "algorithm": ["算法", "排序", "搜索", "优化"],
            "data_structure": ["数据结构", "列表", "树", "图"],
            "web": ["web", "网页", "前端", "后端"],
            "file": ["文件", "读取", "写入", "io"],
            "network": ["网络", "socket", "通信"],
            "security": ["安全", "加密", "认证", "授权"],
            "testing": ["测试", "单元测试", "集成测试"],
            "ml": ["机器学习", "深度学习", "ai", "模型"]
        }
        
        requirement_lower = requirement.lower()
        suggested = []
        
        for tag, keywords in common_tags.items():
            if any(keyword in requirement_lower for keyword in keywords):
                suggested.append(tag)
        
        return suggested
    
    def clear_cache(self):
        """清空嵌入缓存"""
        self._cache.clear()
        logger.info("[Info] 清空嵌入缓存")

