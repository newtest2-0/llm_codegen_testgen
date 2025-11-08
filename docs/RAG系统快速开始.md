# RAG系统快速开始指南

## 🚀 3分钟快速上手

### 1. 启动服务

```bash
python quick_start.py
```

服务启动后，RAG系统自动可用。

### 2. 使用RAG增强代码生成

#### 方式1：自动集成（推荐）

在Web界面中正常使用代码生成功能，系统会自动：
1. 检索知识库中的相似案例
2. 如果找到相关案例，自动使用增强prompt
3. 生成更高质量的代码
4. 代码质量分数>0.8时自动保存到知识库

#### 方式2：手动搜索参考案例

1. 填写项目需求
2. 点击"知识库"按钮（如果有）
3. 搜索相关案例
4. 点击"使用此案例"

### 3. 查看知识库

在浏览器控制台执行：

```javascript
// 打开知识库浏览器
KnowledgeSystem.showBrowser();

// 查看统计信息
KnowledgeSystem.loadStatistics();
```

### 4. 添加知识条目

```javascript
// 手动添加
await KnowledgeSystem.addEntry(
    "实现快速排序算法",
    "def quick_sort(arr): ...",
    "python",
    0.95,
    ["algorithm", "sorting"]
);
```

### 5. 搜索知识库

```javascript
// 搜索相关案例
const results = await KnowledgeSystem.search(
    "排序算法",
    "python",
    5
);
console.log(results);
```

## 📊 使用示例

### 示例1：生成代码并自动保存

1. 输入需求：
```
实现一个二分查找算法，要求：
- 支持升序数组
- 返回目标值的索引
- 如果不存在返回-1
```

2. 生成代码（系统自动检索相似案例）

3. 如果代码质量分数 > 0.8，自动保存到知识库

### 示例2：使用相似案例

1. 输入需求：
```
实现归并排序
```

2. 系统自动检索到之前保存的"快速排序"案例

3. 构建包含参考案例的增强prompt

4. 生成更高质量的归并排序代码

## 🎯 最佳实践

### 1. 积累高质量案例

- 只保存质量分数 > 0.8 的代码
- 确保代码经过测试
- 添加清晰的需求描述

### 2. 合理使用标签

常用标签：
- `algorithm`: 算法
- `database`: 数据库
- `api`: 接口开发
- `file`: 文件操作
- `network`: 网络编程
- `security`: 安全相关

### 3. 定期维护

- 删除错误或过时的条目
- 更新常用案例
- 查看统计信息了解知识库状态

## 🔧 API快速参考

### 添加知识

```bash
POST /api/v1/knowledge/add
{
    "requirement": "需求描述",
    "code": "代码实现",
    "language": "python",
    "tags": ["tag1", "tag2"],
    "quality_score": 0.95
}
```

### 搜索知识

```bash
POST /api/v1/knowledge/search
{
    "query": "搜索关键词",
    "top_k": 5,
    "language": "python"
}
```

### 获取增强Prompt

```bash
POST /api/v1/knowledge/enhanced-prompt
{
    "requirement": "需求描述",
    "language": "python"
}
```

### 获取统计信息

```bash
GET /api/v1/knowledge/statistics
```

## 💡 进阶使用

### 1. 集成到你的代码生成流程

```python
from backend.api.routes.generation_with_rag import generate_with_rag

code, references = await generate_with_rag(
    requirement="实现用户登录",
    language="python",
    provider_manager=provider_manager,
    provider_name="openai",
    use_rag=True
)
```

### 2. 自定义Embedding模型

```python
from sentence_transformers import SentenceTransformer

class CustomEmbedder:
    def __init__(self):
        self.model = SentenceTransformer('your-model')
    
    def embed(self, text):
        return self.model.encode(text).tolist()

retriever = KnowledgeRetriever(knowledge_base, CustomEmbedder())
```

## 🎉 开始使用

现在你已经掌握了RAG系统的基本使用方法，开始积累你的代码知识库吧！

---

**更多详细信息，请查看 [RAG知识库系统说明](RAG知识库系统说明.md)**

