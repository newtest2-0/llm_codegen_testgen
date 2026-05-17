"""
需求管理相关的API路由
支持详细需求、架构设计、详细设计、追溯关系等功能
"""
import uuid
import logging
import json
import os
import shutil
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import io

from core.providers import ProviderManager

logger = logging.getLogger(__name__)

router = APIRouter()

# 图片上传目录（与 app.py 中保持一致）
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# 允许上传的图片类型
ALLOWED_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'}

# ==================== 数据模型 ====================

class RequirementSection(BaseModel):
    """需求文档的单个章节"""
    section_type: str = Field(..., description="章节类型：detailed_requirement, architecture_design, detailed_design, requirement_architecture_trace, requirement_design_trace")
    content: str = Field("", description="章节内容")
    llm_review: Optional[str] = Field(None, description="LLM评阅内容")
    expert_review: Optional[str] = Field(None, description="专家评阅内容")

class RequirementDocument(BaseModel):
    """完整的需求文档"""
    doc_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12], description="文档ID")
    project_name: str = Field("未命名项目", description="项目名称")
    sections: Dict[str, RequirementSection] = Field(default_factory=dict, description="文档章节字典")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")

class LLMReviewRequest(BaseModel):
    """LLM评阅请求"""
    section_type: str = Field(..., description="章节类型")
    content: str = Field(..., description="章节内容")
    provider: Optional[str] = Field(None, description="指定的LLM提供者")

class ExpertReviewRequest(BaseModel):
    """专家评阅请求"""
    section_type: str = Field(..., description="章节类型")
    expert_review: str = Field(..., description="专家评阅内容")

class SectionContentRequest(BaseModel):
    """更新章节内容请求"""
    section_type: str = Field(..., description="章节类型")
    content: str = Field(..., description="章节内容")

class DevelopmentLog(BaseModel):
    """开发日志（严格的JSON Schema）"""
    id: str = Field(..., description="日志ID，格式：模块-类型-序号")
    问题锚点: Dict[str, Any] = Field(..., description="问题锚点信息")
    问题详情: Dict[str, Any] = Field(..., description="问题详细信息")
    解决方案: Dict[str, Any] = Field(..., description="解决方案")
    验证保障: Optional[Dict[str, Any]] = Field(None, description="验证保障")
    元信息: Dict[str, str] = Field(..., description="元信息")

class FixMermaidRequest(BaseModel):
    """Mermaid 修复请求"""
    content: str = Field(..., description="包含 Mermaid 代码块的完整文本")
    provider: Optional[str] = Field(None, description="指定的LLM提供者")

# ==================== 临时内存存储（生产环境应使用数据库）====================
_documents_storage: Dict[str, RequirementDocument] = {}
_logs_storage: List[DevelopmentLog] = []

# ==================== API端点 ====================

@router.post("/documents", response_model=RequirementDocument)
async def create_document(doc: RequirementDocument):
    """创建新的需求文档"""
    doc.doc_id = uuid.uuid4().hex[:12]
    doc.created_at = datetime.now().isoformat()
    doc.updated_at = datetime.now().isoformat()

    _documents_storage[doc.doc_id] = doc
    logger.info(f"创建需求文档: {doc.doc_id} - {doc.project_name}")

    return doc

@router.get("/documents/{doc_id}", response_model=RequirementDocument)
async def get_document(doc_id: str):
    """获取需求文档"""
    if doc_id not in _documents_storage:
        raise HTTPException(status_code=404, detail="文档不存在")

    return _documents_storage[doc_id]

@router.put("/documents/{doc_id}/sections", response_model=RequirementDocument)
async def update_section_content(doc_id: str, request: SectionContentRequest):
    """更新章节内容"""
    if doc_id not in _documents_storage:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc = _documents_storage[doc_id]

    # 如果章节不存在，创建新章节
    if request.section_type not in doc.sections:
        doc.sections[request.section_type] = RequirementSection(
            section_type=request.section_type,
            content=request.content
        )
    else:
        doc.sections[request.section_type].content = request.content

    doc.updated_at = datetime.now().isoformat()
    logger.info(f"更新章节: {doc_id} - {request.section_type}")

    return doc

@router.post("/documents/{doc_id}/llm-review", response_model=Dict)
async def generate_llm_review(doc_id: str, request: LLMReviewRequest, req: Request):
    """
    使用LLM生成评阅内容（复用系统已有的provider配置）

    重要：此功能复用现有的provider系统，不需要额外配置API Key
    """
    if doc_id not in _documents_storage:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 获取provider管理器（复用现有系统配置）
    provider_manager: ProviderManager = req.app.state.provider_manager

    # 选择可用的provider
    available_providers = provider_manager.get_provider_names()

    if not available_providers:
        raise HTTPException(status_code=400, detail="没有可用的AI提供者，请在系统设置中配置API Key")

    # 如果用户指定了provider，使用指定的；否则优先选择有API Key的provider
    if request.provider and request.provider in available_providers:
        selected_provider = request.provider
    else:
        # 优先选择有API Key的provider
        from core.api_key_storage import api_key_storage
        providers_with_keys = [p for p in available_providers if api_key_storage.has_api_key(p)]

        if providers_with_keys:
            selected_provider = providers_with_keys[0]
            logger.info(f"自动选择有API Key的provider: {selected_provider}")
        else:
            selected_provider = available_providers[0]
            logger.warning(f"所有provider都没有API Key，使用第一个: {selected_provider}")

    provider = provider_manager.get_provider(selected_provider)

    # 根据不同的章节类型，生成不同的评阅提示词（包含Mermaid图表）
    section_prompts = {
        "detailed_requirement": """你是专业的软件需求分析师，负责对用户提交的【详细需求描述】进行专业、全面的LLM评阅。

## 一、评阅核心要求
从以下4个维度进行评阅：
- 需求完整性：检查是否覆盖所有核心功能、参与者、业务规则、非功能需求、系统边界
- 需求清晰度：检查描述是否具体、无歧义、有明确示例
- 可测试性：检查是否可转化为可执行的测试用例，有明确的输入输出和验收标准
- 改进建议：给出具体、可落地的优化建议

---

## 二、用例图生成规范（必须严格遵守）

**用例图必须使用 `graph TD`，禁止使用任何其他图表类型。**

唯一允许的语法模板如下，请照此格式生成，不得添加任何其他语法：

```
graph TD
    Actor1["参与者名称"]
    UC1("用例名称1")
    UC2("用例名称2")
    Actor1 --> UC1
    Actor1 --> UC2
```

严格禁止的内容（出现任何一项将导致渲染失败）：
- 禁止 `useCaseDiagram`、`classDiagram` 等非 `graph TD` 图表类型
- 禁止 `<<include>>`、`<<extend>>`、`<>` 等任何含尖括号的语法
- 禁止 `%%` 注释行
- 禁止 `subgraph`、`rectangle`、`system` 等嵌套/分组语法
- 禁止节点别名使用中文（别名只能是英文+数字，如 User、Admin、UC1）
- 禁止空行出现在代码块内部

---

## 三、输出格式（严格按此格式输出）

## 📋 需求评阅

### 1. 需求完整性
（评审内容）

### 2. 需求清晰度
（评审内容）

### 3. 可测试性
（评审内容）

### 4. 改进建议
（改进建议）

## 📊 用例图

```mermaid
graph TD
    Actor1["参与者1"]
    UC1("用例1")
    UC2("用例2")
    Actor1 --> UC1
    Actor1 --> UC2
```

**说明：** 用例图展示了系统的主要参与者和用例之间的关系。

---

以下是需要评阅的详细需求描述：

{content}""",

        "architecture_design": """你是专业的软件架构师，请对以下架构设计进行专业评阅，并生成架构图。

## 架构图生成规范（必须严格遵守）

**架构图必须使用 `graph TB` 或 `graph LR`，禁止使用任何其他图表类型。**

唯一允许的语法模板如下，请照此格式生成：

```
graph TB
    Client[客户端]
    API[API层]
    Service[业务层]
    DB[(数据库)]
    Client --> API
    API --> Service
    Service --> DB
```

严格禁止的内容（出现任何一项将导致渲染失败）：
- 禁止 `%%` 注释行（包括空注释）
- 禁止 `<<include>>`、`<<extend>>`、`<>` 等任何含尖括号的语法
- 禁止 `subgraph`、`rectangle` 等嵌套/分组语法
- 禁止节点别名使用中文（别名只能是英文+数字，如 Client、API、DB）
- 禁止代码块内出现空行

---

以下是需要评阅的架构设计内容：

{content}

---

请严格按以下格式输出评阅报告：

## 📋 架构评阅

### 1. 架构合理性
（评审整体架构是否合理、可扩展）

### 2. 技术选型
（评审技术栈选择是否恰当）

### 3. 模块划分
（评审模块职责是否清晰）

### 4. 潜在风险
（识别可能的技术风险）

### 5. 改进建议
（提出架构优化建议）

## 🏗️ 架构图

```mermaid
graph TB
    Client[客户端]
    API[API层]
    Service[业务层]
    DB[(数据库)]
    Client --> API
    API --> Service
    Service --> DB
```

**说明：** 架构图展示了系统的整体架构和各组件之间的关系。""",

        "detailed_design": """你是专业的软件设计师，请对以下详细设计（接口+参数+返回值）进行专业评阅，并生成序列图。

## 序列图生成规范（必须严格遵守）

唯一允许的语法模板如下，请照此格式生成：

```
sequenceDiagram
    participant C as 客户端
    participant A as API层
    participant D as 数据库
    C->>A: 发起请求
    A->>D: 查询数据
    D-->>A: 返回结果
    A-->>C: 响应数据
```

严格禁止的内容（违反任何一项将导致渲染失败）：
- 禁止消息文本中使用花括号 `{}`，用中文描述代替，例如"传入用户名和密码"而不是"{username,password}"
- 禁止消息文本中使用圆括号 `()`，用中文描述代替
- 禁止消息文本中使用双引号 `"`
- 禁止 `%%` 注释行
- 禁止节点别名使用中文（别名只能是英文+数字）
- 禁止代码块内出现空行
- 消息文本必须简洁，不超过20个字符

---

以下是需要评阅的详细设计内容：

{content}

---

请严格按以下格式输出评阅报告：

## 📋 设计评阅

### 1. 接口设计
（评审接口定义是否合理、RESTful）

### 2. 参数规范
（评审参数类型、必填项是否明确）

### 3. 返回值设计
（评审返回数据结构是否清晰）

### 4. 错误处理
（评审异常情况的处理方案）

### 5. 改进建议
（提出设计优化建议）

## 📈 序列图

```mermaid
sequenceDiagram
    participant C as 客户端
    participant A as API层
    participant D as 数据库
    C->>A: 发起请求
    A->>D: 查询数据
    D-->>A: 返回结果
    A-->>C: 响应数据
```

**说明：** 序列图展示了接口的完整调用流程。""",

        "requirement_architecture_trace": """你是专业的软件需求分析师，请对以下需求→架构追溯关系进行评阅，并生成追溯关系图。

## 追溯关系图生成规范（必须严格遵守）

唯一允许的语法模板如下，请照此格式生成：

```
graph LR
    R1[需求1]
    A1[架构组件1]
    A2[架构组件2]
    R1 --> A1
    R1 --> A2
```

严格禁止的内容：
- 禁止 `%%` 注释行
- 禁止节点别名使用中文（别名只能是英文+数字，如 R1、A1）
- 禁止代码块内出现空行

---

以下是需要评阅的追溯关系内容：

{content}

---

请严格按以下格式输出评阅报告：

## 📋 追溯评阅

### 1. 追溯完整性
（评审是否建立了完整的追溯关系）

### 2. 覆盖度
（评审架构设计是否完全覆盖需求）

### 3. 一致性
（评审追溯关系是否一致）

### 4. 改进建议
（如何优化追溯管理）

## 🔗 追溯关系图

```mermaid
graph LR
    R1[需求1]
    A1[架构组件1]
    A2[架构组件2]
    R1 --> A1
    R1 --> A2
```

**说明：** 追溯关系图展示了需求与架构组件之间的映射关系。""",

        "requirement_design_trace": """你是专业的软件需求分析师，请对以下需求→详细设计追溯关系进行评阅，并生成追溯关系图。

## 追溯关系图生成规范（必须严格遵守）

唯一允许的语法模板如下，请照此格式生成：

```
graph LR
    R1[需求1]
    D1[接口1]
    D2[接口2]
    R1 --> D1
    R1 --> D2
```

严格禁止的内容：
- 禁止 `%%` 注释行
- 禁止节点别名使用中文（别名只能是英文+数字，如 R1、D1）
- 禁止代码块内出现空行

---

以下是需要评阅的追溯关系内容：

{content}

---

请严格按以下格式输出评阅报告：

## 📋 追溯评阅

### 1. 追溯完整性
（评审是否建立了完整的追溯关系）

### 2. 覆盖度
（评审详细设计是否完全覆盖需求）

### 3. 一致性
（评审追溯关系是否一致）

### 4. 改进建议
（如何优化追溯管理）

## 🔗 追溯关系图

```mermaid
graph LR
    R1[需求1]
    D1[接口1]
    D2[接口2]
    R1 --> D1
    R1 --> D2
```

**说明：** 追溯关系图展示了需求与详细设计之间的映射关系。"""
    }

    prompt_template = section_prompts.get(
        request.section_type,
        "请对以下内容进行专业评阅：\n\n{content}\n\n输出格式化的评阅报告。"
    )

    try:
        logger.info(f"使用 {selected_provider} 生成 {request.section_type} 的LLM评阅")

        # 用 replace 替代 format，避免模板中的 {} 被误解析为格式占位符（如 Mermaid 示例中的花括号）
        review_prompt = prompt_template.replace("{content}", request.content)

        # 直接调用 generate()，避免 generate_code() 将 prompt 包装成代码生成模板
        llm_review = await provider.generate(review_prompt)

        # 保存评阅到文档
        doc = _documents_storage[doc_id]
        if request.section_type not in doc.sections:
            doc.sections[request.section_type] = RequirementSection(
                section_type=request.section_type,
                content=request.content
            )

        doc.sections[request.section_type].llm_review = llm_review
        doc.updated_at = datetime.now().isoformat()

        logger.info(f"✅ LLM评阅生成完成: {doc_id} - {request.section_type}")

        # 记录日志（预留接口）
        await _log_llm_review_event(doc_id, request.section_type, selected_provider, "success")

        return {
            "doc_id": doc_id,
            "section_type": request.section_type,
            "llm_review": llm_review,
            "provider": selected_provider,
            "message": "LLM评阅生成成功"
        }

    except Exception as e:
        logger.error(f"❌ LLM评阅生成失败: {e}")

        # 记录错误日志
        await _log_llm_review_event(doc_id, request.section_type, selected_provider, "failed", str(e))

        raise HTTPException(status_code=500, detail=f"LLM评阅生成失败: {str(e)}")

@router.post("/documents/{doc_id}/expert-review", response_model=Dict)
async def save_expert_review(doc_id: str, request: ExpertReviewRequest):
    """保存专家评阅内容"""
    if doc_id not in _documents_storage:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc = _documents_storage[doc_id]

    if request.section_type not in doc.sections:
        doc.sections[request.section_type] = RequirementSection(
            section_type=request.section_type,
            content=""
        )

    doc.sections[request.section_type].expert_review = request.expert_review
    doc.updated_at = datetime.now().isoformat()

    logger.info(f"保存专家评阅: {doc_id} - {request.section_type}")

    return {
        "doc_id": doc_id,
        "section_type": request.section_type,
        "message": "专家评阅保存成功"
    }

@router.get("/documents/{doc_id}/download/{section_type}")
async def download_section(doc_id: str, section_type: str, filename: str = None):
    """下载指定章节的文档，支持自定义文件名（filename 查询参数）"""
    if doc_id not in _documents_storage:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc = _documents_storage[doc_id]

    if section_type not in doc.sections:
        raise HTTPException(status_code=404, detail="章节不存在")

    section = doc.sections[section_type]

    # 生成Markdown格式的文档
    markdown_content = f"""# {_get_section_title(section_type)}

## 项目名称
{doc.project_name}

## 文档ID
{doc.doc_id}

## 创建时间
{doc.created_at}

## 更新时间
{doc.updated_at}

---

## 内容

{section.content or '（暂无内容）'}

---

## LLM评阅

{section.llm_review or '（暂无LLM评阅）'}

---

## 专家评阅

{section.expert_review or '（暂无专家评阅）'}
"""

    # 创建文件流
    file_stream = io.BytesIO(markdown_content.encode('utf-8'))

    # 优先使用前端传入的自定义文件名，否则生成默认名
    if not filename:
        filename = f"文档_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    # 确保以 .md 结尾
    if not filename.lower().endswith('.md'):
        filename += '.md'

    # RFC 5987 编码，兼容中文文件名（Chrome/Firefox/Safari 均支持）
    from urllib.parse import quote
    encoded_filename = quote(filename, safe='')

    return StreamingResponse(
        file_stream,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )

@router.post("/documents/{doc_id}/upload/{section_type}")
async def upload_section(doc_id: str, section_type: str, file: UploadFile = File(...)):
    """上传文档到指定章节（仅接受 .md/.markdown，最大 10MB）"""
    if doc_id not in _documents_storage:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 文件格式校验
    allowed_exts = {'.md', '.markdown'}
    import os
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"文件格式不支持：{ext}，仅接受 .md 或 .markdown 文件")

    # 读取内容并校验大小（10MB）
    MAX_SIZE = 10 * 1024 * 1024
    content_bytes = await file.read()
    if len(content_bytes) > MAX_SIZE:
        raise HTTPException(status_code=413, detail=f"文件过大：{len(content_bytes)/1024/1024:.1f}MB，最大允许 10MB")

    try:
        text_content = content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码错误，请确保文件为 UTF-8 编码")

    doc = _documents_storage[doc_id]

    if section_type not in doc.sections:
        doc.sections[section_type] = RequirementSection(
            section_type=section_type,
            content=text_content
        )
    else:
        doc.sections[section_type].content = text_content

    doc.updated_at = datetime.now().isoformat()

    logger.info(f"上传文档: {doc_id} - {section_type} - {file.filename} ({len(content_bytes)} bytes)")

    return {
        "doc_id": doc_id,
        "section_type": section_type,
        "filename": file.filename,
        "size": len(content_bytes),
        "message": "文档上传成功"
    }

@router.post("/images/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片文件，返回可直接访问的URL路径。
    支持 PNG / JPG / GIF / WebP / SVG / BMP，最大 10MB。
    前端在上传 Markdown 时可同时上传本地图片，拿到 URL 后替换 Markdown 中的本地路径。
    """
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式：{ext}")

    MAX_SIZE = 10 * 1024 * 1024
    content_bytes = await file.read()
    if len(content_bytes) > MAX_SIZE:
        raise HTTPException(status_code=413, detail=f"图片过大：{len(content_bytes)/1024/1024:.1f}MB，最大允许 10MB")

    # 用 UUID 避免文件名冲突，保留原始扩展名
    safe_name = uuid.uuid4().hex + ext
    dest_path = os.path.join(UPLOADS_DIR, safe_name)
    with open(dest_path, "wb") as f:
        f.write(content_bytes)

    logger.info(f"图片上传成功: {file.filename} -> {safe_name}")

    return {
        "filename": safe_name,
        "original_name": file.filename,
        "url": f"/uploads/{safe_name}",
        "size": len(content_bytes),
        "message": "图片上传成功"
    }

# ==================== Mermaid 修复接口 ====================

_MERMAID_FIX_PROMPT = """你是 Mermaid 语法兼容性修复专家，唯一任务是：只修复输入文本中所有的 Mermaid 代码块，确保它们能在所有旧版本 Mermaid 渲染器（v8.x 及以下）上 100% 成功渲染，绝对不能修改文本中除 Mermaid 代码块之外的任何内容。

## 绝对禁止项（违反必渲染失败，发现一个删除一个）
1. 绝对禁止使用 useCaseDiagram 图表类型，强制只能用 graph TD
2. 绝对禁止任何注释：删除所有 %% 开头的行，包括空注释
3. 绝对禁止所有尖括号语法：删除 <<include>>、<<extend>>、<>、<<system>> 等所有带 < 或 > 的内容
4. 绝对禁止任何嵌套结构：删除 {{ ... }}、rectangle "边界" { ... }、system "系统名" { ... } 等所有分组和边界
5. 绝对禁止节点名称包含特殊字符：只能保留中文、英文、数字和下划线，删除所有全角标点、半角标点、空格、换行
6. 绝对禁止箭头标注超过 5 个汉字，过长的标注直接删除
7. 绝对禁止代码块内有空行，所有空行全部删除
8. 绝对禁止节点别名使用中文，别名必须是纯英文（如 User、Admin、UC1、UC2）

## 必须遵守的唯一正确语法
1. 图表开头必须且只能是：graph TD
2. 参与者节点格式：别名["角色名称"]（如 User["普通用户"]）
3. 用例节点格式：别名("用例名称")（如 UC1("登录系统")）
4. 关联关系格式：别名 --> 别名（如 User --> UC1）
5. 可选关系标注：别名 -->|短标注| 别名（标注不超过 5 字）
6. 每个节点定义和每条箭头连接必须各自独占一行
7. 所有节点和箭头直接写在根层级，不使用任何分组
8. 优先保留核心参与者（不超过3个）和核心用例（不超过8个），非核心内容直接删除

## 兜底机制（强制触发）
如果原始代码过于复杂无法修正，或者修正后仍可能存在渲染风险，直接返回下面这个固定的极简示例代码，不要尝试任何复杂的修改：
```mermaid
graph TD
    User["用户"]
    UC1("核心功能")
    User --> UC1
```

## 修正步骤（严格按顺序执行）
1. 从输入文本中精准定位所有以 ```mermaid 开头、以 ``` 结尾的代码块
2. 提取每个代码块中的纯代码内容
3. 按照上面的【绝对禁止项】逐条检查并删除所有违规内容
4. 按照上面的【必须遵守的唯一正确语法】重新组织剩余的有效内容
5. 如果修正后代码行数少于 3 行（即没有有效内容），直接使用兜底示例代码
6. 将修正后的代码重新包装成 ```mermaid ... ``` 代码块
7. 用修正后的代码块替换原始文本中的对应代码块
8. 绝对不能修改文本中除 Mermaid 代码块之外的任何内容，包括评阅报告的文字、标题、格式等

现在，请处理下面的输入文本：

{content}"""


@router.post("/fix-mermaid", response_model=Dict)
async def fix_mermaid(request: FixMermaidRequest, req: Request):
    """
    使用 LLM 修复文本中的 Mermaid 代码块，确保在旧版本渲染器（v8.x）上 100% 渲染成功。
    只修改 Mermaid 代码块，不改动其他内容。
    """
    provider_manager: ProviderManager = req.app.state.provider_manager
    available_providers = provider_manager.get_provider_names()

    if not available_providers:
        raise HTTPException(status_code=400, detail="没有可用的AI提供者，请在系统设置中配置API Key")

    if request.provider and request.provider in available_providers:
        selected_provider = request.provider
    else:
        from core.api_key_storage import api_key_storage
        providers_with_keys = [p for p in available_providers if api_key_storage.has_api_key(p)]
        selected_provider = providers_with_keys[0] if providers_with_keys else available_providers[0]

    provider = provider_manager.get_provider(selected_provider)

    try:
        logger.info(f"使用 {selected_provider} 修复 Mermaid 代码块")
        fix_prompt = _MERMAID_FIX_PROMPT.replace("{content}", request.content)
        fixed_content = await provider.generate(fix_prompt)

        logger.info("Mermaid 修复完成")
        return {
            "fixed_content": fixed_content,
            "provider": selected_provider,
            "message": "Mermaid 修复成功"
        }

    except Exception as e:
        logger.error(f"Mermaid 修复失败: {e}")
        raise HTTPException(status_code=500, detail=f"Mermaid 修复失败: {str(e)}")


# ==================== 日志记录接口（预留）====================

@router.post("/logs", response_model=Dict)
async def create_development_log(log: DevelopmentLog):
    """
    记录开发日志（预留接口）

    使用严格的JSON Schema，确保字段完整性
    """
    try:
        # 验证日志结构的完整性
        _validate_log_schema(log)

        # 存储日志
        _logs_storage.append(log)

        logger.info(f"记录开发日志: {log.id}")

        return {
            "log_id": log.id,
            "message": "日志记录成功",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"日志记录失败: {e}")
        raise HTTPException(status_code=400, detail=f"日志记录失败: {str(e)}")

@router.get("/logs", response_model=List[DevelopmentLog])
async def get_all_logs():
    """获取所有开发日志（预留接口）"""
    return _logs_storage

@router.get("/logs/{log_id}", response_model=DevelopmentLog)
async def get_log(log_id: str):
    """获取指定的开发日志（预留接口）"""
    for log in _logs_storage:
        if log.id == log_id:
            return log

    raise HTTPException(status_code=404, detail="日志不存在")

# ==================== 辅助函数 ====================

def _get_section_title(section_type: str) -> str:
    """获取章节标题"""
    titles = {
        "detailed_requirement": "详细需求描述",
        "architecture_design": "架构设计",
        "detailed_design": "详细设计（含接口+参数+返回值）",
        "requirement_architecture_trace": "需求→架构追溯",
        "requirement_design_trace": "需求→详细设计追溯"
    }
    return titles.get(section_type, section_type)

async def _log_llm_review_event(doc_id: str, section_type: str, provider: str, status: str, error: str = None):
    """
    记录LLM评阅事件到日志系统（预留）

    此函数演示如何使用严格的JSON Schema记录日志
    """
    try:
        log_id = f"llm-review-{uuid.uuid4().hex[:6]}"

        log = DevelopmentLog(
            id=log_id,
            问题锚点={
                "关联模块": "需求管理模块",
                "技术栈": "Python 3.9 + FastAPI",
                "问题类型": "LLM评阅" if status == "success" else "运行时错误",
                "问题特征词": ["LLM评阅", provider, section_type]
            },
            问题详情={
                "触发场景": f"对文档 {doc_id} 的 {section_type} 章节执行LLM评阅",
                "错误表现": {
                    "错误日志": error or "无错误",
                    "功能影响": "LLM评阅失败" if status == "failed" else "正常"
                },
                "影响范围": f"文档 {doc_id} 的 {section_type} 章节"
            },
            解决方案={
                "错误原因分析": error or "正常执行",
                "解决思路": "使用系统已有的provider配置调用LLM",
                "代码对比": {
                    "修正前代码": "",
                    "修正后代码": "",
                    "关键步骤": ["复用provider系统", "调用generate_code方法", "保存评阅结果"]
                }
            },
            验证保障={
                "测试用例": [],
                "验收标准": [f"LLM评阅{status}"]
            },
            元信息={
                "来源": "需求管理模块自动记录",
                "更新时间": datetime.now().strftime("%H:%M:%S，%Y-%m-%d")
            }
        )

        _logs_storage.append(log)
        logger.debug(f"日志记录成功: {log_id}")

    except Exception as e:
        logger.error(f"日志记录失败: {e}")

def _validate_log_schema(log: DevelopmentLog):
    """验证日志结构的完整性"""
    # 验证问题锚点
    required_anchor_fields = ["关联模块", "技术栈", "问题类型", "问题特征词"]
    for field in required_anchor_fields:
        if field not in log.问题锚点:
            raise ValueError(f"问题锚点缺少必填字段: {field}")

    # 验证问题详情
    required_detail_fields = ["触发场景", "错误表现", "影响范围"]
    for field in required_detail_fields:
        if field not in log.问题详情:
            raise ValueError(f"问题详情缺少必填字段: {field}")

    # 验证解决方案
    required_solution_fields = ["错误原因分析", "解决思路", "代码对比"]
    for field in required_solution_fields:
        if field not in log.解决方案:
            raise ValueError(f"解决方案缺少必填字段: {field}")

    # 验证元信息
    required_meta_fields = ["来源", "更新时间"]
    for field in required_meta_fields:
        if field not in log.元信息:
            raise ValueError(f"元信息缺少必填字段: {field}")

    logger.debug("日志结构验证通过")
