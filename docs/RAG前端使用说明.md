# RAG知识库系统 - 前端使用说明

## 📱 前端入口

### 方式1：点击"知识库"按钮（推荐）

在主界面顶部导航栏，可以看到：

```
[代码生成] [知识库 NEW] [测试生成] [代码评估] [系统设置]
```

点击 **"知识库"** 按钮，即可打开知识库浏览器。

### 方式2：浏览器控制台

按 `F12` 打开浏览器控制台，输入：

```javascript
KnowledgeSystem.showBrowser();
```

### 方式3：通过URL直接访问API

```
http://localhost:8000/docs#/知识库
```

可以在Swagger文档中测试所有知识库API。

## 🖥️ 知识库浏览器界面

### 界面布局

```
┌─────────────────────────────────────────────────────┐
│  🗄️ 知识库浏览器                          [×]      │
├─────────────────────────────────────────────────────┤
│  搜索框: [____________]  [所有语言▼]  [🔍 搜索]    │
├─────────────────────────────────────────────────────┤
│  统计信息                                           │
│  ┌─────┬─────┬─────┬─────┐                         │
│  │ 10  │ 0.85│  3  │  8  │                         │
│  │总数 │质量 │语言 │标签 │                         │
│  └─────┴─────┴─────┴─────┘                         │
├─────────────────────────────────────────────────────┤
│  知识条目列表                                       │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ [Python] [质量: 92%] [algorithm] [sorting] │  │
│  │ 实现一个快速排序算法...                     │  │
│  │ [查看代码▼] [使用] [🗑️]                     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ [Python] [质量: 88%] [api] [web]           │  │
│  │ 实现用户认证系统...                         │  │
│  │ [查看代码▼] [使用] [🗑️]                     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [🔄 刷新]                              [关闭]     │
└─────────────────────────────────────────────────────┘
```

### 功能说明

#### 1. 搜索栏
- **文本搜索**：输入需求关键词
- **语言过滤**：选择特定编程语言
- **实时搜索**：输入后点击搜索按钮

#### 2. 统计面板
- **总数**：知识库中的总条目数
- **平均质量**：所有条目的平均质量分数
- **语言种类**：支持的编程语言数量
- **标签种类**：所有标签的数量

#### 3. 条目列表
每个条目显示：
- **语言标签**：编程语言
- **质量分数**：代码质量（0-100%）
- **标签**：分类标签
- **需求摘要**：需求描述的前200字
- **操作按钮**：
  - `查看代码` - 展开查看完整代码
  - `使用` - 将案例加载到当前需求
  - `删除` - 删除此条目

## 🤖 RAG使用的AI模型

### 关键点：RAG复用你已配置的AI模型！

RAG系统**不需要单独配置AI**，它使用的是你在"系统设置"中已经配置的AI模型。

### AI使用场景

#### 1. 生成增强Prompt（主要用途）

当你生成代码时，RAG系统会：

```javascript
// 1. 检索知识库
const results = await retriever.retrieve(requirement, language);

// 2. 如果找到相似案例
if (results.length > 0) {
    // 3. 构建增强的prompt
    const enhancedPrompt = `
        请根据以下需求生成代码。
        
        我已经为你提供了3个相似的参考案例：
        
        案例1: (相似度: 0.92, 质量: 0.95)
        需求：${results[0].requirement}
        代码：${results[0].code}
        
        案例2: (相似度: 0.88, 质量: 0.90)
        需求：${results[1].requirement}
        代码：${results[1].code}
        
        当前需求：${requirement}
        
        请参考上述案例，生成高质量代码。
    `;
    
    // 4. 使用增强prompt调用AI
    const code = await provider.generate_code(enhancedPrompt, language);
}
```

#### 2. 使用的AI提供者

RAG会使用第一个可用的AI提供者，例如：

```python
# backend/api/routes/knowledge.py
provider_manager = request.app.state.provider_manager
provider_names = provider_manager.get_provider_names()

# 使用第一个可用的提供者
provider_name = provider_names[0]  # 例如 "openai", "deepseek" 等
provider = provider_manager.get_provider(provider_name)

# 调用AI生成增强prompt
response = await provider.generate(diagram_prompt)
```

### 你可以使用的AI模型

根据你的配置，RAG可以使用：

- **OpenAI** (gpt-4o-mini) - 如果配置了OpenAI密钥
- **DeepSeek** (deepseek-chat) - 如果配置了DeepSeek密钥
- **Claude** (claude-3-5-sonnet) - 如果配置了Anthropic密钥
- **Gemini** (gemini-1.5-flash) - 如果配置了Google密钥
- **通义千问** (qwen-plus) - 如果配置了阿里云密钥
- **百川智能** (Baichuan4) - 如果配置了百川密钥
- **ChatGLM** (glm-4-plus) - 如果配置了智谱密钥
- **LLaMA** (llama3.1:8b) - 如果配置了Ollama

## 💡 实际使用流程

### 完整流程示例

```
1. 用户输入需求：
   "实现一个二分查找算法"

2. RAG系统自动工作：
   [前端] 发送请求到 /api/v1/generation/generate
   [后端] 检测到需求，触发RAG检索
   [RAG] 搜索知识库，找到3个相似案例
   
3. 构建增强Prompt：
   原始: "实现一个二分查找算法"
   增强: "实现一个二分查找算法\n\n参考案例1...\n参考案例2...\n参考案例3..."

4. 调用AI生成：
   [AI] 收到增强prompt，生成高质量代码
   [AI] 参考了3个成功案例的设计思路
   
5. 质量检查：
   [系统] 代码质量分数: 0.92
   [RAG] 超过阈值0.8，自动保存到知识库
   
6. 下次遇到类似问题：
   [RAG] 可以检索到刚才保存的案例
   [AI] 代码质量持续提升！
```

## 🎯 使用技巧

### 1. 手动搜索参考案例

在生成代码前，先搜索知识库：

```javascript
// 1. 打开知识库
KnowledgeSystem.showBrowser();

// 2. 搜索相关案例
// 输入关键词，例如 "排序"

// 3. 点击"使用"按钮
// 案例会自动填充到需求输入框

// 4. 修改需求并生成代码
```

### 2. 手动添加优质案例

如果你有特别好的代码实现：

```javascript
await KnowledgeSystem.addEntry(
    "实现用户认证系统，支持JWT",
    "def authenticate(token): ...",
    "python",
    0.95,  // 质量分数
    ["security", "api", "auth"]
);
```

### 3. 查看统计信息

了解知识库状态：

```javascript
// 在浏览器控制台
await KnowledgeSystem.loadStatistics();

// 或通过API
fetch('http://localhost:8000/api/v1/knowledge/statistics')
    .then(r => r.json())
    .then(data => console.log(data));
```

## 🔧 开发者选项

### 查看RAG工作日志

打开浏览器控制台（F12），可以看到：

```
[Knowledge] 知识库系统初始化...
[Knowledge] 找到 3 条相关记录
[Knowledge] 生成增强prompt，参考 3 个案例
[RAG] 使用增强prompt生成代码
[RAG] 高质量代码已自动保存: abc123
```

### 直接调用API

```javascript
// 获取增强prompt
const enhanced = await fetch('http://localhost:8000/api/v1/knowledge/enhanced-prompt', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        requirement: "实现快速排序",
        language: "python",
        top_k: 3
    })
});

const data = await enhanced.json();
console.log(data.enhanced_prompt);
console.log(data.references);
```

## 📊 效果对比

### 没有RAG的情况

```
用户: "实现归并排序"
AI: 生成基础代码（质量70%）
问题: 可能缺少边界处理、注释不全
```

### 使用RAG的情况

```
用户: "实现归并排序"
RAG: 找到3个排序算法的成功案例
AI: 参考案例生成高质量代码（质量90%）
优势: 完整的错误处理、清晰的注释、最佳实践
```

## 🎉 开始使用

1. **启动系统**：`python quick_start.py`
2. **打开浏览器**：访问 http://localhost:8080
3. **点击"知识库"按钮**：开始探索RAG系统！

---

**RAG系统让AI从过往经验中学习，每次生成都比上次更好！** 🚀

