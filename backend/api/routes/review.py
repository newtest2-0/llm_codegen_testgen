"""
审阅API路由 - 处理LLM评阅和专家评阅相关请求
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import re

# 创建路由器
router = APIRouter(prefix="/review", tags=["review"])
logger = logging.getLogger(__name__)


# 请求模型
class LLMReviewRequest(BaseModel):
    field_type: str
    content: str
    field_name: str


class ReviewResponse(BaseModel):
    success: bool
    review: Optional[str] = None
    score: Optional[int] = None
    suggestions: List[str] = []
    field_type: Optional[str] = None
    field_name: Optional[str] = None
    error: Optional[str] = None


@router.post('/llm', response_model=ReviewResponse)
async def llm_review(review_request: LLMReviewRequest, request: Request):
    """
    LLM评阅接口
    接收用户提交的内容,通过LLM进行评阅和分析
    """
    try:
        # 获取参数
        field_type = review_request.field_type
        content = review_request.content
        field_name = review_request.field_name
        
        if not content:
            raise HTTPException(status_code=400, detail='内容不能为空')
        
        logger.info(f"收到LLM评阅请求 - 字段类型: {field_type}, 内容长度: {len(content)}")
        
        # 根据不同字段类型构建评阅提示词
        review_prompt = build_review_prompt(field_type, content, field_name)
        
        # 调用LLM进行评阅
        try:
            # 从request.app.state获取provider_manager
            provider_manager = request.app.state.provider_manager
            
            # 使用第一个可用的provider
            provider_names = provider_manager.get_provider_names()
            if not provider_names:
                return ReviewResponse(
                    success=False,
                    error='没有可用的LLM服务,请先配置API密钥'
                )
            
            provider_name = provider_names[0]
            provider = provider_manager.get_provider(provider_name)
            
            # 发送评阅请求
            response = await provider.generate(review_prompt)
            
            # 解析评阅结果
            review_result = parse_review_response(response, field_type)
            
            return ReviewResponse(
                success=True,
                review=review_result.get('review', ''),
                score=review_result.get('score'),
                suggestions=review_result.get('suggestions', []),
                field_type=field_type,
                field_name=field_name
            )
            
        except Exception as e:
            logger.error(f"LLM评阅失败: {str(e)}")
            return ReviewResponse(
                success=False,
                error=f'LLM评阅失败: {str(e)}'
            )
        
    except Exception as e:
        logger.error(f"处理LLM评阅请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def build_review_prompt(field_type: str, content: str, field_name: str) -> str:
    """
    根据字段类型构建评阅提示词
    """
    
    base_prompts = {
        'requirement': """
你是一位资深的需求分析专家。请评审以下需求描述,关注:
1. 需求的完整性和清晰度
2. 是否包含必要的问题细节(触发场景、错误表现、影响范围)
3. 是否有歧义或模糊的表述
4. 是否缺少关键信息

需求内容:
{content}

请提供:
1. 整体评价
2. 质量评分(0-100分)
3. 具体的改进建议(列表形式)
""",
        
        'architecture': """
你是一位资深的系统架构师。请评审以下架构设计,关注:
1. 架构设计的合理性和可行性
2. 技术选型是否恰当
3. 模块划分是否清晰
4. 是否考虑了非功能性需求(性能、安全、可扩展性)
5. 是否有架构风险或潜在问题

架构设计内容:
{content}

请提供:
1. 整体评价
2. 质量评分(0-100分)
3. 具体的改进建议(列表形式)
""",
        
        'design': """
你是一位资深的软件工程师。请评审以下详细设计和代码实现,关注:
1. 代码实现的正确性
2. 错误原因分析是否准确
3. 解决方案是否有效
4. 代码质量(可读性、可维护性)
5. 是否遵循最佳实践
6. 是否有潜在的bug或安全问题

详细设计内容:
{content}

请提供:
1. 整体评价
2. 质量评分(0-100分)
3. 具体的改进建议(列表形式)
""",
        
        'trace_arch': """
你是一位资深的系统工程师。请评审以下需求到架构的追溯关系,关注:
1. 追溯关系是否完整和准确
2. 问题到架构决策的映射是否合理
3. 是否遗漏了关键的追溯链路
4. 架构决策是否真正解决了问题

追溯关系内容:
{content}

请提供:
1. 整体评价
2. 质量评分(0-100分)
3. 具体的改进建议(列表形式)
""",
        
        'trace_design': """
你是一位资深的软件工程师。请评审以下需求到详细设计的追溯关系,关注:
1. 追溯关系是否完整和准确
2. 问题到代码实现的映射是否合理
3. 是否清晰标注了修改点
4. 测试验证是否充分

追溯关系内容:
{content}

请提供:
1. 整体评价
2. 质量评分(0-100分)
3. 具体的改进建议(列表形式)
"""
    }
    
    prompt_template = base_prompts.get(field_type, base_prompts['requirement'])
    return prompt_template.format(content=content)


def parse_review_response(response: str, field_type: str) -> Dict[str, Any]:
    """
    解析LLM的评审响应
    """
    result = {
        'review': response,
        'score': None,
        'suggestions': []
    }
    
    # 尝试提取评分
    score_patterns = [
        r'评分[:：]\s*(\d+)',
        r'得分[:：]\s*(\d+)',
        r'(\d+)\s*分',
        r'(\d+)/100'
    ]
    
    for pattern in score_patterns:
        match = re.search(pattern, response)
        if match:
            try:
                result['score'] = int(match.group(1))
                break
            except:
                pass
    
    # 尝试提取建议列表
    suggestion_section = None
    if '改进建议' in response:
        suggestion_section = response.split('改进建议')[1]
    elif '建议' in response:
        suggestion_section = response.split('建议')[1]
    
    if suggestion_section:
        # 提取列表项
        lines = suggestion_section.split('\n')
        for line in lines:
            line = line.strip()
            # 匹配列表项(数字、字母、符号开头)
            if re.match(r'^[\d\.\-\*•]+\s+', line):
                suggestion = re.sub(r'^[\d\.\-\*•]+\s+', '', line)
                if suggestion:
                    result['suggestions'].append(suggestion)
    
    return result


class SaveReviewRequest(BaseModel):
    field_type: str
    content: str
    review_data: Dict[str, Any]


@router.post('/save')
async def save_review(save_request: SaveReviewRequest):
    """
    保存评审记录
    """
    try:
        # 这里可以保存到数据库
        # 目前先返回成功响应,前端会保存到localStorage
        
        return {
            'success': True,
            'message': '评审记录已保存'
        }
        
    except Exception as e:
        logger.error(f"保存评审记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/history/{field_type}')
async def get_review_history(field_type: str):
    """
    获取评审历史记录
    """
    try:
        # 这里可以从数据库查询
        # 目前返回空列表,前端会从localStorage读取
        
        return {
            'success': True,
            'data': []
        }
        
    except Exception as e:
        logger.error(f"获取评审历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class GenerateDiagramRequest(BaseModel):
    content: str
    diagram_type: str
    module_id: str


class DiagramResponse(BaseModel):
    success: bool
    diagram_code: Optional[str] = None
    error: Optional[str] = None


@router.post('/generate-diagram', response_model=DiagramResponse)
async def generate_diagram(diagram_request: GenerateDiagramRequest, request: Request):
    """
    生成UML图表 - 基于文本内容生成Mermaid图表代码
    """
    try:
        content = diagram_request.content
        diagram_type = diagram_request.diagram_type
        module_id = diagram_request.module_id
        
        if not content:
            raise HTTPException(status_code=400, detail='内容不能为空')
        
        logger.info(f"收到图表生成请求 - 类型: {diagram_type}, 模块: {module_id}")
        
        # 构建图表生成提示词
        diagram_prompt = build_diagram_prompt(content, diagram_type, module_id)
        
        try:
            # 从request.app.state获取provider_manager
            provider_manager = request.app.state.provider_manager
            
            # 使用第一个可用的provider
            provider_names = provider_manager.get_provider_names()
            if not provider_names:
                return DiagramResponse(
                    success=False,
                    error='没有可用的LLM服务,请先配置API密钥'
                )
            
            provider_name = provider_names[0]
            provider = provider_manager.get_provider(provider_name)
            
            # 发送图表生成请求
            response = await provider.generate(diagram_prompt)
            
            # 提取Mermaid代码
            diagram_code = extract_mermaid_code(response)
            
            return DiagramResponse(
                success=True,
                diagram_code=diagram_code
            )
            
        except Exception as e:
            logger.error(f"图表生成失败: {str(e)}")
            return DiagramResponse(
                success=False,
                error=f'图表生成失败: {str(e)}'
            )
        
    except Exception as e:
        logger.error(f"处理图表生成请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def build_diagram_prompt(content: str, diagram_type: str, module_id: str) -> str:
    """
    构建图表生成提示词
    """
    
    prompts = {
        'usecase': """
你是一位UML专家。请根据以下需求描述生成用例图的Mermaid代码。

需求内容:
{content}

要求:
1. 使用Mermaid的graph语法
2. 清晰展示参与者(Actor)和用例(Use Case)
3. 使用箭头表示关系
4. 添加适当的样式和颜色
5. 只输出Mermaid代码,不要有其他说明文字

示例格式:
graph TD
    A[用户] -->|登录| B(认证系统)
    A -->|查询| C(数据查询)
    B --> D{验证成功?}
    D -->|是| E[进入系统]
    D -->|否| F[返回错误]
    
    style A fill:#e1f5ff
    style B fill:#fff4e1

现在请生成:
""",
        
        'component': """
你是一位软件架构师。请根据以下架构设计生成组件图的Mermaid代码。

架构内容:
{content}

要求:
1. 使用Mermaid的graph语法
2. 展示系统的主要组件和层次
3. 使用subgraph表示不同层级
4. 清晰标注组件间的依赖关系
5. 只输出Mermaid代码

示例格式:
graph TB
    subgraph "前端层"
        UI[用户界面]
        Controller[控制器]
    end
    
    subgraph "业务层"
        Service[业务服务]
    end
    
    subgraph "数据层"
        DB[(数据库)]
    end
    
    UI --> Controller --> Service --> DB

现在请生成:
""",
        
        'class': """
你是一位软件设计专家。请根据以下详细设计生成类图的Mermaid代码。

设计内容:
{content}

要求:
1. 使用Mermaid的classDiagram语法
2. 包含类的属性和方法
3. 展示类之间的关系(继承、组合、依赖等)
4. 只输出Mermaid代码

示例格式:
classDiagram
    class User {
        +String username
        +String email
        +login()
        +logout()
    }
    
    class Database {
        +Connection conn
        +query()
        +execute()
    }
    
    User --> Database

现在请生成:
""",
        
        'sequence': """
你是一位系统分析师。请根据以下追溯关系生成序列图的Mermaid代码。

追溯内容:
{content}

要求:
1. 使用Mermaid的sequenceDiagram语法
2. 清晰展示参与者之间的交互顺序
3. 标注方法调用和返回
4. 只输出Mermaid代码

示例格式:
sequenceDiagram
    participant User
    participant Service
    participant DB
    
    User->>Service: 请求数据
    Service->>DB: 查询
    DB-->>Service: 返回结果
    Service-->>User: 响应

现在请生成:
""",
        
        'flowchart': """
你是一位流程分析专家。请根据以下追溯关系生成流程图的Mermaid代码。

追溯内容:
{content}

要求:
1. 使用Mermaid的graph LR或graph TD语法
2. 清晰展示流程的步骤和决策点
3. 使用不同形状表示不同类型的节点
4. 只输出Mermaid代码

示例格式:
graph LR
    A[开始] --> B[处理]
    B --> C{判断}
    C -->|是| D[继续]
    C -->|否| E[结束]
    D --> E

现在请生成:
"""
    }
    
    prompt_template = prompts.get(diagram_type, prompts['flowchart'])
    return prompt_template.format(content=content)


def extract_mermaid_code(response: str) -> str:
    """
    从LLM响应中提取Mermaid代码
    """
    # 尝试提取代码块中的内容
    
    # 匹配 ```mermaid ... ``` 或 ``` ... ```
    patterns = [
        r'```mermaid\s*([\s\S]*?)\s*```',
        r'```\s*((?:graph|classDiagram|sequenceDiagram|flowchart)[\s\S]*?)\s*```',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # 如果没有代码块,尝试直接查找Mermaid关键字
    if any(keyword in response for keyword in ['graph', 'classDiagram', 'sequenceDiagram', 'flowchart']):
        # 提取从关键字开始到结尾的内容
        for keyword in ['graph TD', 'graph LR', 'classDiagram', 'sequenceDiagram', 'flowchart']:
            if keyword in response:
                start_idx = response.find(keyword)
                return response[start_idx:].strip()
    
    # 如果都没有,返回原始响应
    return response.strip()


class CodeFromDiagramRequest(BaseModel):
    diagram_code: str
    text_content: Optional[str] = ""
    module_id: str
    diagram_type: str


class CodeGenerationResponse(BaseModel):
    success: bool
    generated_code: Optional[str] = None
    explanation: Optional[str] = None
    suggestions: List[str] = []
    error: Optional[str] = None


@router.post('/code-from-diagram', response_model=CodeGenerationResponse)
async def generate_code_from_diagram(code_request: CodeFromDiagramRequest, request: Request):
    """
    基于UML图表生成代码 - 核心功能
    """
    try:
        diagram_code = code_request.diagram_code
        text_content = code_request.text_content
        module_id = code_request.module_id
        diagram_type = code_request.diagram_type
        
        if not diagram_code:
            raise HTTPException(status_code=400, detail='图表代码不能为空')
        
        logger.info(f"收到基于图表生成代码请求 - 类型: {diagram_type}, 模块: {module_id}")
        
        # 构建代码生成提示词
        code_prompt = build_code_from_diagram_prompt(diagram_code, text_content, diagram_type)
        
        try:
            provider_manager = request.app.state.provider_manager
            provider_names = provider_manager.get_provider_names()
            
            if not provider_names:
                return CodeGenerationResponse(
                    success=False,
                    error='没有可用的LLM服务,请先配置API密钥'
                )
            
            provider_name = provider_names[0]
            provider = provider_manager.get_provider(provider_name)
            
            # 发送代码生成请求
            response = await provider.generate(code_prompt)
            
            # 提取生成的代码
            generated_code = extract_python_code(response)
            
            return CodeGenerationResponse(
                success=True,
                generated_code=generated_code,
                explanation='代码已基于UML图表结构生成，包含完整的类定义、方法实现和错误处理。',
                suggestions=[
                    '请验证生成的代码是否符合图表设计',
                    '建议添加单元测试验证功能',
                    '检查是否需要补充异常处理逻辑',
                    '确认是否符合项目的编码规范'
                ]
            )
            
        except Exception as e:
            logger.error(f"基于图表生成代码失败: {str(e)}")
            return CodeGenerationResponse(
                success=False,
                error=f'代码生成失败: {str(e)}'
            )
        
    except Exception as e:
        logger.error(f"处理代码生成请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def build_code_from_diagram_prompt(diagram_code: str, text_content: str, diagram_type: str) -> str:
    """
    构建基于图表生成代码的提示词
    """
    
    base_prompt = f"""
你是一位资深的软件工程师。请根据以下UML图表生成高质量的Python代码。

图表类型: {diagram_type}

UML图表（Mermaid格式）:
{diagram_code}

{f'补充说明:\n{text_content}\n' if text_content else ''}

要求:
1. 严格按照图表中定义的类、方法、属性生成代码
2. 包含完整的类定义和方法实现
3. 添加适当的类型注解（Type Hints）
4. 添加必要的文档字符串（Docstrings）
5. 实现基本的错误处理逻辑
6. 遵循PEP 8编码规范
7. 代码应该是可运行的，而不只是框架
8. 只输出Python代码，不要有其他说明文字

请生成代码:
"""
    
    return base_prompt


def extract_python_code(response: str) -> str:
    """
    从LLM响应中提取Python代码
    """
    
    # 匹配 ```python ... ``` 或 ``` ... ```
    patterns = [
        r'```python\s*([\s\S]*?)\s*```',
        r'```\s*((?:class|def|import)[\s\S]*?)\s*```',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # 如果没有代码块,尝试直接查找Python关键字
    if any(keyword in response for keyword in ['class ', 'def ', 'import ']):
        # 提取看起来像Python代码的部分
        lines = response.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if any(line.strip().startswith(kw) for kw in ['class ', 'def ', 'import ', 'from ']):
                in_code = True
            if in_code:
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines).strip()
    
    # 返回原始响应
    return response.strip()


class ValidateConsistencyRequest(BaseModel):
    diagrams: Dict[str, str]


class ConsistencyResponse(BaseModel):
    success: bool
    is_consistent: bool
    message: str
    issues: List[str] = []
    suggestions: List[str] = []
    error: Optional[str] = None


@router.post('/validate-consistency', response_model=ConsistencyResponse)
async def validate_diagram_consistency(validate_request: ValidateConsistencyRequest, request: Request):
    """
    验证多个图表之间的一致性
    """
    try:
        diagrams = validate_request.diagrams
        
        if len(diagrams) < 2:
            raise HTTPException(status_code=400, detail='至少需要2个图表')
        
        logger.info(f"收到一致性验证请求 - 图表数量: {len(diagrams)}")
        
        # 构建验证提示词
        validation_prompt = build_validation_prompt(diagrams)
        
        try:
            provider_manager = request.app.state.provider_manager
            provider_names = provider_manager.get_provider_names()
            
            if not provider_names:
                return ConsistencyResponse(
                    success=False,
                    is_consistent=False,
                    message='没有可用的LLM服务',
                    error='请先配置API密钥'
                )
            
            provider_name = provider_names[0]
            provider = provider_manager.get_provider(provider_name)
            
            # 发送验证请求
            response = await provider.generate(validation_prompt)
            
            # 解析验证结果
            validation_result = parse_validation_response(response)
            
            return ConsistencyResponse(
                success=True,
                is_consistent=validation_result['is_consistent'],
                message=validation_result['message'],
                issues=validation_result['issues'],
                suggestions=validation_result['suggestions']
            )
            
        except Exception as e:
            logger.error(f"一致性验证失败: {str(e)}")
            return ConsistencyResponse(
                success=False,
                is_consistent=False,
                message='验证过程出错',
                error=str(e)
            )
        
    except Exception as e:
        logger.error(f"处理一致性验证请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def build_validation_prompt(diagrams: Dict[str, str]) -> str:
    """
    构建一致性验证提示词
    """
    
    diagrams_text = ""
    for module_id, diagram_code in diagrams.items():
        module_names = {
            'detailedRequirement': '需求用例图',
            'architectureDesign': '架构组件图',
            'detailedDesign': '详细设计类图'
        }
        diagrams_text += f"\n### {module_names.get(module_id, module_id)}:\n{diagram_code}\n"
    
    prompt = f"""
你是一位软件工程专家。请分析以下多个UML图表之间的一致性。

{diagrams_text}

请验证:
1. 用例图中的参与者和用例是否在组件图中有对应的组件？
2. 组件图中的组件是否在类图中有对应的类？
3. 类图中的类和关系是否合理？
4. 整体设计是否存在矛盾或遗漏？

请以JSON格式回复（不要用代码块包裹）:
{{
  "is_consistent": true/false,
  "message": "整体评价",
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}}
"""
    
    return prompt


def parse_validation_response(response: str) -> Dict[str, Any]:
    """
    解析验证响应
    """
    import json
    
    result = {
        'is_consistent': True,
        'message': '图表一致性验证完成',
        'issues': [],
        'suggestions': []
    }
    
    try:
        # 尝试提取JSON
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, response)
        
        if match:
            parsed = json.loads(match.group(0))
            result.update(parsed)
        else:
            # 如果没有JSON，尝试解析文本
            result['message'] = response
            
            if '不一致' in response or '问题' in response or '错误' in response:
                result['is_consistent'] = False
            
            # 尝试提取问题列表
            if '问题' in response:
                issues_section = response.split('问题')[1] if '问题' in response else ''
                lines = issues_section.split('\n')
                for line in lines[:5]:  # 最多提取5个问题
                    line = line.strip()
                    if line and re.match(r'^[\d\.\-\*•]+\s+', line):
                        issue = re.sub(r'^[\d\.\-\*•]+\s+', '', line)
                        if issue:
                            result['issues'].append(issue)
    
    except Exception as e:
        logger.error(f"解析验证响应失败: {str(e)}")
        result['message'] = '验证完成，但解析结果时出错'
    
    return result

