# RAG存储与检索机制详解

## 📁 JSON文件存储位置

### 默认存储路径

```
项目根目录/
└── data/
    └── knowledge_base.json  ← RAG知识库存储在这里
```

**完整路径示例**：
```
C:\Users\h7187\Desktop\clone\llm_codegen_testgen-9\data\knowledge_base.json
```

### 配置位置

在 `backend/core/rag/knowledge_base.py` 中定义：

```python
class KnowledgeBase:
    def __init__(self, storage_path: str = "data/knowledge_base.json"):
        self.storage_path = Path(storage_path)
        self.entries: List[KnowledgeEntry] = []
        self._ensure_storage_dir()  # 自动创建data目录
        self.load()  # 启动时自动加载
```

### 自动创建机制

```python
def _ensure_storage_dir(self):
    """确保存储目录存在"""
    self.storage_path.parent.mkdir(parents=True, exist_ok=True)
```

- 如果 `data/` 目录不存在，系统会**自动创建**
- 如果 `knowledge_base.json` 不存在，首次保存时会**自动创建**

## 📄 JSON文件结构

### 完整结构示例

```json
{
  "version": "1.0",
  "updated_at": "2024-11-08T12:00:00",
  "count": 3,
  "entries": [
    {
      "id": "abc123",
      "requirement": "实现快速排序算法...",
      "code": "def quick_sort(arr): ...",
      "language": "python",
      "tags": ["algorithm", "sorting"],
      "quality_score": 0.92,
      "test_results": {
        "passed": true,
        "coverage": 0.95
      },
      "metadata": {
        "auto_saved": true,
        "provider": "openai"
      },
      "created_at": "2024-11-08T10:30:00"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | string | 知识库格式版本 |
| `updated_at` | string | 最后更新时间 |
| `count` | number | 知识条目总数 |
| `entries` | array | 知识条目数组 |

### 单个条目结构

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | string | 唯一标识符 | "abc123" |
| `requirement` | string | 需求描述 | "实现快速排序..." |
| `code` | string | 代码实现 | "def quick_sort..." |
| `language` | string | 编程语言 | "python" |
| `tags` | array | 标签数组 | ["algorithm", "sorting"] |
| `quality_score` | float | 质量分数(0-1) | 0.92 |
| `test_results` | object | 测试结果 | {...} |
| `metadata` | object | 元数据 | {...} |
| `created_at` | string | 创建时间 | "2024-11-08..." |

## 🔍 检索机制详解

### 1. 加载流程

系统启动时自动加载知识库：

```python
# backend/api/routes/knowledge.py
knowledge_base = KnowledgeBase("data/knowledge_base.json")
embedder = TextEmbedder()
retriever = KnowledgeRetriever(knowledge_base, embedder)
```

**加载步骤**：
```
启动后端 → 初始化KnowledgeBase → 读取JSON文件 → 解析为Python对象 → 存储在内存
```

### 2. 检索工作流程

完整的检索流程：

```python
# Step 1: 用户输入需求
requirement = "实现归并排序"

# Step 2: 文本向量化
query_vector = embedder.embed(requirement)
# 结果: [0.23, 0.45, 0.67, ..., 0.12]  # 384维向量

# Step 3: 遍历所有知识条目
for entry in knowledge_base.entries:
    # 将每个条目的需求也向量化
    entry_vector = embedder.embed(entry.requirement)
    
    # 计算余弦相似度
    similarity = cosine_similarity(query_vector, entry_vector)
    
    # 综合评分 = 相似度 × (0.7 + 0.3 × 质量分数)
    score = similarity * (0.7 + 0.3 * entry.quality_score)
    
    results.append((entry, score))

# Step 4: 按分数排序，返回Top K
results.sort(key=lambda x: x[1], reverse=True)
return results[:top_k]
```

### 3. 相似度计算

#### 文本嵌入（Embedding）

```python
# backend/core/rag/embedder.py
def embed(self, text: str) -> List[float]:
    """将文本转换为384维向量"""
    # 简化实现：基于哈希和统计特征
    words = text.lower().split()
    # ... 生成向量
    return vector  # [0.23, 0.45, ..., 0.12]
```

#### 余弦相似度

```python
def cosine_similarity(vec1, vec2):
    """计算两个向量的余弦相似度"""
    # 点积
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # 模长
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    # 余弦相似度 = 点积 / (模长1 × 模长2)
    return dot_product / (norm1 * norm2)
```

**相似度范围**：0 到 1
- **1.0**：完全相同
- **0.8-0.9**：非常相似
- **0.6-0.7**：比较相似
- **<0.5**：不太相似

### 4. 实际检索示例

假设用户输入：**"实现归并排序"**

#### 检索过程

```python
# 1. 向量化查询
query = "实现归并排序"
query_vec = [0.2, 0.5, 0.3, ...]  # 384维

# 2. 与知识库对比
知识库条目1: "实现快速排序算法"
  条目向量: [0.25, 0.48, 0.35, ...]
  相似度: 0.87 (很相似！都是排序算法)
  质量分数: 0.92
  综合评分: 0.87 × (0.7 + 0.3 × 0.92) = 0.85

知识库条目2: "实现用户认证系统"
  条目向量: [0.05, 0.12, 0.08, ...]
  相似度: 0.15 (不相似)
  质量分数: 0.88
  综合评分: 0.15 × (0.7 + 0.3 × 0.88) = 0.14

知识库条目3: "实现二分查找算法"
  条目向量: [0.18, 0.35, 0.22, ...]
  相似度: 0.65 (有点相似，都是算法)
  质量分数: 0.95
  综合评分: 0.65 × (0.7 + 0.3 × 0.95) = 0.64

# 3. 排序并返回Top 3
结果:
  1. 快速排序 (0.85) ← 最相关
  2. 二分查找 (0.64)
  3. 用户认证 (0.14)
```

## 💾 保存机制

### 自动保存触发

```python
# backend/api/routes/generation_with_rag.py
async def auto_save_to_knowledge_base(
    requirement: str,
    code: str,
    language: str,
    quality_score: float
):
    # 质量阈值检查
    QUALITY_THRESHOLD = 0.80
    
    if quality_score < QUALITY_THRESHOLD:
        logger.info(f"[RAG] 质量分数 {quality_score:.2f} 未达到阈值")
        return None
    
    # 自动建议标签
    tags = retriever.suggest_tags(requirement)
    
    # 保存到知识库
    entry_id = knowledge_base.add_entry(
        requirement=requirement,
        code=code,
        language=language,
        tags=tags,
        quality_score=quality_score
    )
    
    # 写入JSON文件
    knowledge_base.save()  # ← 这里触发文件写入
```

### 保存流程

```python
def save(self):
    """保存知识库到JSON文件"""
    data = {
        "version": "1.0",
        "updated_at": datetime.now().isoformat(),
        "count": len(self.entries),
        "entries": [entry.to_dict() for entry in self.entries]
    }
    
    # 写入文件
    with open(self.storage_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[OK] 保存知识库: {len(self.entries)} 条记录")
```

## 🔄 完整工作流程

### 场景1：首次使用

```
1. 启动系统
   → 检查 data/knowledge_base.json
   → 文件不存在
   → 创建空知识库 entries = []

2. 用户生成代码
   → 代码质量 0.92 (高质量!)
   → 触发自动保存

3. 保存到JSON
   → 创建第一个条目
   → 写入 data/knowledge_base.json
   → 文件内容: {"entries": [第一个条目]}
```

### 场景2：后续使用（有知识积累）

```
1. 启动系统
   → 加载 data/knowledge_base.json
   → 解析10条已有知识
   → 存储在内存: entries = [条目1, 条目2, ..., 条目10]

2. 用户输入需求: "实现归并排序"
   
3. RAG自动检索
   → 向量化查询 "实现归并排序"
   → 遍历10条知识
   → 计算相似度
   → 找到最相关的3条:
      - 快速排序 (0.87)
      - 堆排序 (0.82)
      - 二分查找 (0.65)

4. 构建增强Prompt
   原始: "实现归并排序"
   增强: "实现归并排序\n\n参考案例1: 快速排序...\n参考案例2: 堆排序..."

5. 生成高质量代码
   → 质量 0.93
   → 自动保存为第11条知识
   → 更新 data/knowledge_base.json

6. 下次使用时
   → 加载11条知识
   → 可以检索到刚才保存的归并排序
   → 知识库越来越丰富！
```

## 🎯 性能优化

### 1. 内存缓存

```python
class KnowledgeRetriever:
    def __init__(self):
        self._cache: Dict[str, List[float]] = {}  # 嵌入缓存
    
    def _get_embedding(self, text: str):
        if text not in self._cache:
            self._cache[text] = self.embedder.embed(text)
        return self._cache[text]
```

**避免重复计算**：
- 第一次查询 "快速排序" → 计算向量 → 缓存
- 第二次查询 "快速排序" → 直接从缓存读取 ⚡

### 2. 增量保存

```python
def add_entry(self, ...):
    # 添加条目到内存
    self.entries.append(entry)
    
    # 立即保存到文件
    self.save()  # 每次添加都保存，避免丢失数据
```

### 3. 懒加载

```python
def load(self):
    """启动时才加载，不使用时不占用内存"""
    if self.storage_path.exists():
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.entries = [KnowledgeEntry.from_dict(e) for e in data["entries"]]
```

## 📊 实际文件查看

### 查看知识库文件

**Windows**:
```powershell
# 查看文件
Get-Content data\knowledge_base.json | ConvertFrom-Json

# 或直接用文本编辑器打开
notepad data\knowledge_base.json
```

**Linux/Mac**:
```bash
# 查看文件
cat data/knowledge_base.json | jq '.'

# 或
less data/knowledge_base.json
```

### 通过API查看

```bash
# 获取统计信息
curl http://localhost:8000/api/v1/knowledge/statistics

# 列出所有条目
curl http://localhost:8000/api/v1/knowledge/list?limit=10
```

### 通过前端查看

1. 打开浏览器：http://localhost:8080
2. 点击"知识库"按钮
3. 查看所有保存的知识条目

## 🔧 手动管理JSON文件

### 备份知识库

```bash
# 创建备份
cp data/knowledge_base.json data/knowledge_base_backup_2024-11-08.json
```

### 清空知识库

```bash
# 删除文件（系统会重新创建空的）
rm data/knowledge_base.json

# 或通过API清空
curl -X POST http://localhost:8000/api/v1/knowledge/clear
```

### 导入知识库

```python
# 从其他JSON文件导入
import json
from backend.core.rag import KnowledgeBase

# 读取旧数据
with open('old_knowledge.json', 'r') as f:
    old_data = json.load(f)

# 添加到新知识库
kb = KnowledgeBase()
for entry_data in old_data['entries']:
    entry = KnowledgeEntry.from_dict(entry_data)
    kb.entries.append(entry)

kb.save()
```

## 🎉 总结

### RAG存储机制

- **位置**：`data/knowledge_base.json`
- **格式**：标准JSON格式
- **自动创建**：首次使用时自动创建
- **持久化**：每次修改立即保存

### RAG检索机制

- **加载**：启动时一次性加载到内存
- **向量化**：将文本转换为384维向量
- **相似度**：计算余弦相似度（0-1）
- **排序**：综合相似度和质量分数排序
- **返回**：返回Top K最相关的知识

### 性能特点

- **快速**：内存检索，毫秒级响应
- **智能**：基于语义相似度，不是简单关键词匹配
- **可扩展**：支持替换为专业embedding模型

---

**现在你知道知识存在哪里，以及系统如何找到它了！** 🚀

