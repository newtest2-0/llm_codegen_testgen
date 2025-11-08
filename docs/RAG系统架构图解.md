# RAG系统架构图解

## 📁 JSON文件实际位置

```
C:\Users\h7187\Desktop\clone\llm_codegen_testgen-9\
└── data\
    └── knowledge_base.json  ← RAG知识库就在这里！（已创建）
```

## 📄 实际JSON文件内容（已生成）

```json
{
  "version": "1.0",
  "updated_at": "2025-11-08T10:33:39",
  "count": 3,
  "entries": [
    {
      "id": "27df3449-205b-4db6-b3c0-83bd0588ce07",
      "requirement": "实现快速排序算法，支持升序降序",
      "code": "def quick_sort(arr, reverse=False):...",
      "language": "python",
      "tags": ["algorithm", "sorting"],
      "quality_score": 0.92,
      "test_results": {"passed": true, "coverage": 0.95},
      "created_at": "2025-11-08T10:33:39"
    },
    {
      "id": "dc7ec086-5cfc-4f21-80b5-72279512fe56",
      "requirement": "实现二分查找算法，在有序数组中查找目标值",
      "code": "def binary_search(arr, target):...",
      "language": "python",
      "tags": ["algorithm", "search"],
      "quality_score": 0.95,
      "created_at": "2025-11-08T10:33:39"
    },
    {
      "id": "29ad3a76-27fd-45b0-aa9c-47bbf0c02d55",
      "requirement": "实现用户认证系统，支持JWT token",
      "code": "import jwt\ndef authenticate(username, password):...",
      "language": "python",
      "tags": ["security", "api"],
      "quality_score": 0.88,
      "created_at": "2025-11-08T10:33:39"
    }
  ]
}
```

## 🔍 RAG如何扫描检索？

### 完整流程图

```
┌──────────────────────────────────────────────────┐
│  启动系统: python quick_start.py                │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  后端启动: backend/api/routes/knowledge.py      │
│                                                  │
│  knowledge_base = KnowledgeBase(                │
│      "data/knowledge_base.json"                 │
│  )                                               │
│                                                  │
│  执行 knowledge_base.load()                     │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  加载JSON文件到内存                             │
│                                                  │
│  with open("data/knowledge_base.json") as f:    │
│      data = json.load(f)                        │
│                                                  │
│  self.entries = [                               │
│      快速排序对象,                               │
│      二分查找对象,                               │
│      用户认证对象                                │
│  ]                                               │
│                                                  │
│  ✅ 3条知识已加载到内存！                        │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  用户发起查询: "实现归并排序算法"                │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  向量化查询                                      │
│                                                  │
│  query_vec = embedder.embed("实现归并排序")     │
│  → [0.23, 0.45, 0.67, ..., 0.12]  (384维)      │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  遍历内存中的3条知识（不读文件，内存计算）      │
│                                                  │
│  知识1: 快速排序                                │
│    向量: [0.25, 0.48, 0.35, ..., 0.15]         │
│    相似度 = cosine(query_vec, 知识1_vec)       │
│          = 0.87  ← 很相似！                     │
│    综合分 = 0.87 × (0.7 + 0.3×0.92) = 0.85    │
│                                                  │
│  知识2: 二分查找                                │
│    相似度 = 0.65                                │
│    综合分 = 0.64                                │
│                                                  │
│  知识3: 用户认证                                │
│    相似度 = 0.15  ← 不相关                      │
│    综合分 = 0.14                                │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  排序并返回Top 3                                │
│                                                  │
│  结果 = [                                        │
│    (快速排序, 0.85),  ← 最相关                  │
│    (二分查找, 0.64),                            │
│    (用户认证, 0.14)                             │
│  ]                                               │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  构建增强Prompt                                  │
│                                                  │
│  prompt = f"""                                   │
│  参考案例1: 快速排序                            │
│  {快速排序的代码}                                │
│                                                  │
│  参考案例2: 二分查找                            │
│  {二分查找的代码}                                │
│                                                  │
│  当前需求: 实现归并排序                         │
│  """                                             │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  调用AI生成代码（使用你配置的AI模型）           │
│                                                  │
│  provider.generate_code(enhanced_prompt)        │
│                                                  │
│  AI看到2个成功案例 → 生成高质量代码             │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│  自动保存高质量代码                             │
│                                                  │
│  if quality_score > 0.8:                        │
│      kb.add_entry(归并排序, code, ...)          │
│      ↓                                           │
│      entries.append(新条目)  ← 添加到内存        │
│      ↓                                           │
│      kb.save()  ← 写入JSON文件                   │
│      ↓                                           │
│      data/knowledge_base.json更新                │
│      ↓                                           │
│      现在有4条知识了！                           │
└──────────────────────────────────────────────────┘
```

## 🎯 关键点总结

### 1. JSON文件位置
```
项目根目录\data\knowledge_base.json
```

**实际路径**：
```
C:\Users\h7187\Desktop\clone\llm_codegen_testgen-9\data\knowledge_base.json
```

**查看命令**：
```powershell
notepad data\knowledge_base.json
```

### 2. 扫描机制

**不是每次都扫描文件！而是：**

```
系统启动 → 读取JSON一次 → 加载到内存 → 之后都在内存中检索
              ↑                              ↓
              └─────── 新增知识时写回文件 ←──┘
```

**性能**：
- 加载文件：1次（启动时）
- 检索速度：毫秒级（内存检索）
- 写入文件：仅在添加/修改时

### 3. AI使用方式

RAG**不需要额外配置AI**，复用你已有的AI模型：

```python
# 获取你在系统设置中配置的AI
provider_manager = request.app.state.provider_manager
provider_names = provider_manager.get_provider_names()
# ['openai', 'deepseek', 'claude', ...]

# 使用第一个可用的
provider = provider_manager.get_provider(provider_names[0])

# 用增强的prompt调用AI
code = await provider.generate_code(enhanced_prompt)
```

## 📊 实际数据展示

演示脚本已经创建了3条知识：

| ID | 需求 | 语言 | 质量 | 标签 |
|----|----|------|------|------|
| 27df... | 快速排序 | Python | 0.92 | algorithm, sorting |
| dc7e... | 二分查找 | Python | 0.95 | algorithm, search |
| 29ad... | 用户认证 | Python | 0.88 | security, api |

**文件大小**：约3KB（3条记录）

## 🚀 立即体验

### 1. 查看JSON文件
```bash
notepad data\knowledge_base.json
```

### 2. 启动系统
```bash
python quick_start.py
```

### 3. 打开知识库
- 访问：http://localhost:8080
- 点击顶部紫色的【知识库 NEW】按钮
- 查看3条演示知识

### 4. 测试检索
```javascript
// 浏览器控制台
await KnowledgeSystem.search("排序算法", "python", 5);
```

---

**现在你完全理解了！** 🎉

- **存储位置**：`data/knowledge_base.json`（已创建，3条记录）
- **检索方式**：内存检索，毫秒级响应
- **AI模型**：复用你已配置的模型，无需额外配置

