"""
需求管理相关的API路由
支持详细需求、架构设计、详细设计、追溯关系等功能
"""
import uuid
import logging
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import io

from core.providers import ProviderManager

logger = logging.getLogger(__name__)

router = APIRouter()

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
        "detailed_requirement": """请对以下详细需求描述进行专业评阅，并生成用例图：

{content}

请按以下格式输出：

## 📋 需求评阅

从以下方面进行评审：
1. 需求完整性：是否涵盖了所有必要的功能点
2. 需求清晰度：描述是否明确、无歧义
3. 可测试性：需求是否可被验证
4. 改进建议：提出具体的优化建议

## 📊 用例图

```mermaid
graph TD
    %% 请根据需求描述生成用例图
    %% 示例：
    User[用户] -->|操作| Function[功能]
```

**说明：** 用例图展示了系统的主要参与者和用例之间的关系。""",

        "architecture_design": """请对以下架构设计进行专业评阅，并生成架构图：

{content}

请按以下格式输出：

## 📋 架构评阅

从以下方面进行评审：
1. 架构合理性：整体架构是否合理、可扩展
2. 技术选型：技术栈选择是否恰当
3. 模块划分：模块职责是否清晰
4. 潜在风险：识别可能的技术风险
5. 改进建议：提出架构优化建议

## 🏗️ 架构图

```mermaid
graph TB
    %% 请根据架构描述生成架构图
    %% 示例：
    Client[客户端] --> API[API层]
    API --> Service[业务层]
    Service --> DB[(数据库)]
```

**说明：** 架构图展示了系统的整体架构和各组件之间的关系。""",

        "detailed_design": """请对以下详细设计（接口+参数+返回值）进行专业评阅，并生成类图和序列图：

{content}

请按以下格式输出：

## 📋 设计评阅

从以下方面进行评审：
1. 接口设计：接口定义是否合理、RESTful
2. 参数规范：参数类型、必填项是否明确
3. 返回值设计：返回数据结构是否清晰
4. 错误处理：异常情况的处理方案
5. 改进建议：提出设计优化建议

## 🏗️ 类图

```mermaid
classDiagram
    %% 请根据设计描述生成类图
    %% 示例：
    class User {
        +String id
        +String name
        +login()
        +logout()
    }
```

## 📈 序列图

```mermaid
sequenceDiagram
    %% 请根据接口调用流程生成序列图
    %% 示例：
    participant Client
    participant API
    participant DB
    Client->>API: 请求
    API->>DB: 查询
    DB-->>API: 返回数据
    API-->>Client: 响应
```

**说明：** 类图展示了系统的数据模型，序列图展示了接口的调用流程。""",

        "requirement_architecture_trace": """请对以下需求→架构追溯关系进行评阅，并生成追溯矩阵图：

{content}

请按以下格式输出：

## 📋 追溯评阅

从以下方面进行评审：
1. 追溯完整性：是否建立了完整的追溯关系
2. 覆盖度：架构设计是否完全覆盖需求
3. 一致性：追溯关系是否一致
4. 改进建议：如何优化追溯管理

## 🔗 追溯关系图

```mermaid
graph LR
    %% 请根据追溯关系生成追溯图
    %% 示例：
    R1[需求1] --> A1[架构组件1]
    R1 --> A2[架构组件2]
    R2[需求2] --> A2
```

**说明：** 追溯关系图展示了需求与架构组件之间的映射关系。""",

        "requirement_design_trace": """请对以下需求→详细设计追溯关系进行评阅，并生成追溯矩阵图：

{content}

请按以下方面进行评审：
1. 追溯完整性：是否建立了完整的追溯关系
2. 覆盖度：详细设计是否完全覆盖需求
3. 一致性：追溯关系是否一致
4. 改进建议：如何优化追溯管理

## 🔗 追溯关系图

```mermaid
graph LR
    %% 请根据追溯关系生成追溯图
    %% 示例：
    R1[需求1] --> D1[接口1]
    R1 --> D2[接口2]
    R2[需求2] --> D2
```

**说明：** 追溯关系图展示了需求与详细设计之间的映射关系。"""
    }

    prompt_template = section_prompts.get(
        request.section_type,
        "请对以下内容进行专业评阅：\n\n{content}\n\n输出格式化的评阅报告。"
    )

    review_prompt = prompt_template.format(content=request.content)

    try:
        logger.info(f"使用 {selected_provider} 生成 {request.section_type} 的LLM评阅")

        # 调用provider生成评阅（复用现有的generate_code方法）
        llm_review = await provider.generate_code(
            requirement=review_prompt,
            language="text",
            extra_directives="输出专业、结构化的评阅报告，使用中文"
        )

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
async def download_section(doc_id: str, section_type: str):
    """下载指定章节的文档"""
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

    filename = f"{doc.project_name}_{section_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    return StreamingResponse(
        file_stream,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.post("/documents/{doc_id}/upload/{section_type}")
async def upload_section(doc_id: str, section_type: str, file: UploadFile = File(...)):
    """上传文档到指定章节"""
    if doc_id not in _documents_storage:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 读取文件内容
    content = await file.read()
    text_content = content.decode('utf-8')

    doc = _documents_storage[doc_id]

    if section_type not in doc.sections:
        doc.sections[section_type] = RequirementSection(
            section_type=section_type,
            content=text_content
        )
    else:
        doc.sections[section_type].content = text_content

    doc.updated_at = datetime.now().isoformat()

    logger.info(f"上传文档: {doc_id} - {section_type} - {file.filename}")

    return {
        "doc_id": doc_id,
        "section_type": section_type,
        "filename": file.filename,
        "message": "文档上传成功"
    }

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
