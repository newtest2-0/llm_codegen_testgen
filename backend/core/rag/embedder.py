"""
文本嵌入模块
将文本转换为向量，用于相似度搜索
"""
import hashlib
from typing import List
import logging

logger = logging.getLogger(__name__)


class TextEmbedder:
    """文本嵌入器（简化版）"""
    
    def __init__(self):
        """初始化嵌入器"""
        self.vector_dim = 384  # 向量维度
    
    def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        注意：这是一个简化实现，使用基于哈希的伪向量
        生产环境建议使用真实的embedding模型，如：
        - sentence-transformers
        - OpenAI embeddings
        - HuggingFace transformers
        """
        # 简化实现：基于文本特征生成伪向量
        # 实际应用中应该使用真实的embedding模型
        
        # 提取文本特征
        words = text.lower().split()
        word_count = len(words)
        char_count = len(text)
        unique_words = len(set(words))
        
        # 生成哈希向量
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # 转换为浮点向量
        vector = []
        for i in range(0, len(hash_bytes), 2):
            if len(vector) >= self.vector_dim:
                break
            byte_val = hash_bytes[i:i+2]
            normalized = int.from_bytes(byte_val, 'big') / 65535.0
            vector.append(normalized)
        
        # 填充到固定维度
        while len(vector) < self.vector_dim:
            vector.append(0.0)
        
        # 添加统计特征
        vector[0] = min(word_count / 100.0, 1.0)
        vector[1] = min(char_count / 1000.0, 1.0)
        vector[2] = min(unique_words / 100.0, 1.0)
        
        return vector[:self.vector_dim]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            raise ValueError("向量维度不匹配")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入"""
        return [self.embed(text) for text in texts]


class SimpleEmbedder(TextEmbedder):
    """
    简单嵌入器
    
    使用基于关键词的简单相似度计算
    适合快速原型和不需要深度学习的场景
    """
    
    def calculate_keyword_similarity(self, text1: str, text2: str) -> float:
        """基于关键词计算相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        # Jaccard相似度
        return len(intersection) / len(union) if union else 0.0


# 提供使用真实embedding模型的建议
RECOMMENDED_MODELS = """
推荐的Embedding模型：

1. sentence-transformers (推荐)
   pip install sentence-transformers
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')

2. OpenAI Embeddings
   pip install openai
   import openai
   response = openai.Embedding.create(input=text, model="text-embedding-ada-002")

3. HuggingFace Transformers
   pip install transformers torch
   from transformers import AutoTokenizer, AutoModel
   tokenizer = AutoTokenizer.from_pretrained('bert-base-chinese')
   model = AutoModel.from_pretrained('bert-base-chinese')

当前使用简化版本，适合快速原型开发。
生产环境建议安装上述模型以获得更好的性能。
"""

logger.info("[Info] 文本嵌入器初始化完成")
logger.info("[Info] 当前使用简化版embedding，建议安装专业模型")

