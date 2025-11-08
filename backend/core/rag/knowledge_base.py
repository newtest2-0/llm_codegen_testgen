"""
知识库管理模块
存储和管理项目经验
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class KnowledgeEntry:
    """知识条目"""
    
    def __init__(
        self,
        requirement: str,
        code: str,
        language: str,
        tags: List[str],
        quality_score: float,
        test_results: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        entry_id: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        self.id = entry_id or str(uuid.uuid4())
        self.requirement = requirement
        self.code = code
        self.language = language
        self.tags = tags
        self.quality_score = quality_score
        self.test_results = test_results or {}
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "requirement": self.requirement,
            "code": self.code,
            "language": self.language,
            "tags": self.tags,
            "quality_score": self.quality_score,
            "test_results": self.test_results,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntry':
        """从字典创建"""
        return cls(
            requirement=data["requirement"],
            code=data["code"],
            language=data["language"],
            tags=data["tags"],
            quality_score=data["quality_score"],
            test_results=data.get("test_results"),
            metadata=data.get("metadata"),
            entry_id=data.get("id"),
            created_at=data.get("created_at")
        )


class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(self, storage_path: str = "data/knowledge_base.json"):
        self.storage_path = Path(storage_path)
        self.entries: List[KnowledgeEntry] = []
        self._ensure_storage_dir()
        self.load()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self):
        """从文件加载知识库"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entries = [
                        KnowledgeEntry.from_dict(entry) 
                        for entry in data.get("entries", [])
                    ]
                logger.info(f"[OK] 加载知识库: {len(self.entries)} 条记录")
            except Exception as e:
                logger.error(f"[ERROR] 加载知识库失败: {e}")
                self.entries = []
        else:
            logger.info("[Info] 知识库文件不存在，创建新知识库")
            self.entries = []
    
    def save(self):
        """保存知识库到文件"""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "count": len(self.entries),
                "entries": [entry.to_dict() for entry in self.entries]
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[OK] 保存知识库: {len(self.entries)} 条记录")
            return True
        except Exception as e:
            logger.error(f"[ERROR] 保存知识库失败: {e}")
            return False
    
    def add_entry(
        self,
        requirement: str,
        code: str,
        language: str,
        tags: List[str],
        quality_score: float,
        test_results: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加知识条目"""
        entry = KnowledgeEntry(
            requirement=requirement,
            code=code,
            language=language,
            tags=tags,
            quality_score=quality_score,
            test_results=test_results,
            metadata=metadata
        )
        
        self.entries.append(entry)
        self.save()
        
        logger.info(f"[OK] 添加知识条目: {entry.id}")
        return entry.id
    
    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """获取知识条目"""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def delete_entry(self, entry_id: str) -> bool:
        """删除知识条目"""
        original_count = len(self.entries)
        self.entries = [e for e in self.entries if e.id != entry_id]
        
        if len(self.entries) < original_count:
            self.save()
            logger.info(f"[OK] 删除知识条目: {entry_id}")
            return True
        
        logger.warning(f"[WARN] 未找到知识条目: {entry_id}")
        return False
    
    def update_entry(
        self,
        entry_id: str,
        **kwargs
    ) -> bool:
        """更新知识条目"""
        entry = self.get_entry(entry_id)
        if not entry:
            return False
        
        # 更新属性
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        self.save()
        logger.info(f"[OK] 更新知识条目: {entry_id}")
        return True
    
    def search_by_tags(self, tags: List[str]) -> List[KnowledgeEntry]:
        """按标签搜索"""
        results = []
        for entry in self.entries:
            if any(tag in entry.tags for tag in tags):
                results.append(entry)
        return results
    
    def search_by_language(self, language: str) -> List[KnowledgeEntry]:
        """按语言搜索"""
        return [e for e in self.entries if e.language == language]
    
    def get_top_quality(self, limit: int = 10) -> List[KnowledgeEntry]:
        """获取高质量条目"""
        sorted_entries = sorted(
            self.entries,
            key=lambda x: x.quality_score,
            reverse=True
        )
        return sorted_entries[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.entries:
            return {
                "total": 0,
                "languages": {},
                "avg_quality": 0.0,
                "tags": {}
            }
        
        languages = {}
        tags = {}
        total_quality = 0.0
        
        for entry in self.entries:
            # 语言统计
            languages[entry.language] = languages.get(entry.language, 0) + 1
            
            # 标签统计
            for tag in entry.tags:
                tags[tag] = tags.get(tag, 0) + 1
            
            # 质量统计
            total_quality += entry.quality_score
        
        return {
            "total": len(self.entries),
            "languages": languages,
            "avg_quality": total_quality / len(self.entries),
            "tags": tags,
            "storage_path": str(self.storage_path),
            "last_updated": datetime.now().isoformat()
        }
    
    def clear(self):
        """清空知识库"""
        self.entries = []
        self.save()
        logger.info("[Info] 知识库已清空")

