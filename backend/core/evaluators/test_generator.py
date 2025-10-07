"""
智能测试用例生成器
"""
import ast
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from ..providers import ProviderManager

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """代码分析器，用于分析生成的代码结构"""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.variables = []
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        分析代码结构
        
        Args:
            code: Python代码字符串
            
        Returns:
            代码分析结果
        """
        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "main_function": None,
            "return_type": "unknown",
            "parameters": [],
            "complexity": "simple"
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self._analyze_function(node)
                    analysis["functions"].append(func_info)
                    
                    # 检查是否是主函数（solve函数）
                    if node.name == "solve":
                        analysis["main_function"] = func_info
                        analysis["parameters"] = func_info["parameters"]
                        analysis["return_type"] = func_info["return_type"]
                
                elif isinstance(node, ast.ClassDef):
                    analysis["classes"].append({
                        "name": node.name,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        analysis["imports"].append(f"{module}.{alias.name}")
            
            # 分析复杂度
            analysis["complexity"] = self._estimate_complexity(tree)
            
        except SyntaxError as e:
            logger.warning(f"代码语法错误，无法分析: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _analyze_function(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析函数节点"""
        func_info = {
            "name": func_node.name,
            "parameters": [],
            "return_type": "unknown",
            "docstring": None,
            "has_loops": False,
            "has_conditions": False
        }
        
        # 分析参数
        for arg in func_node.args.args:
            param_info = {"name": arg.arg, "type": "unknown"}
            if arg.annotation:
                param_info["type"] = self._get_annotation_string(arg.annotation)
            func_info["parameters"].append(param_info)
        
        # 分析返回类型
        if func_node.returns:
            func_info["return_type"] = self._get_annotation_string(func_node.returns)
        
        # 获取文档字符串
        if (func_node.body and 
            isinstance(func_node.body[0], ast.Expr) and 
            isinstance(func_node.body[0].value, ast.Constant) and 
            isinstance(func_node.body[0].value.value, str)):
            func_info["docstring"] = func_node.body[0].value.value
        
        # 分析函数体结构
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                func_info["has_loops"] = True
            elif isinstance(node, (ast.If, ast.IfExp)):
                func_info["has_conditions"] = True
        
        return func_info
    
    def _get_annotation_string(self, annotation) -> str:
        """获取类型注解字符串"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        else:
            return "unknown"
    
    def _estimate_complexity(self, tree: ast.AST) -> str:
        """估算代码复杂度"""
        complexity_score = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                complexity_score += 2
            elif isinstance(node, ast.If):
                complexity_score += 1
            elif isinstance(node, (ast.Try, ast.With)):
                complexity_score += 1
            elif isinstance(node, ast.FunctionDef):
                complexity_score += len(node.args.args)
        
        if complexity_score <= 3:
            return "simple"
        elif complexity_score <= 8:
            return "moderate"
        else:
            return "complex"

class IntelligentTestGenerator:
    """智能测试用例生成器"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
        self.analyzer = CodeAnalyzer()
    
    async def generate_tests_for_code(self, code: str, requirement: str, 
                                    provider_name: Optional[str] = None,
                                    role: str = "developer",
                                    role_prompt: Optional[str] = None) -> str:
        """
        根据具体代码生成测试用例
        
        Args:
            code: 生成的代码
            requirement: 原始需求
            provider_name: 指定的AI提供者
            role: 开发角色
            role_prompt: 角色提示词
            
        Returns:
            生成的测试代码
        """
        # 分析代码结构
        analysis = self.analyzer.analyze_code(code)
        
        if "error" in analysis:
            # 如果代码有语法错误，生成基础测试
            return self._generate_basic_test(requirement)
        
        # 构建智能测试提示（基于角色）
        test_prompt = self._build_role_based_test_prompt(code, analysis, requirement, role, role_prompt)
        
        # 选择提供者
        if not provider_name:
            provider_name = self.provider_manager.get_provider_names()[0]
        
        provider = self.provider_manager.get_provider(provider_name)
        if not provider:
            logger.error(f"提供者 {provider_name} 不可用")
            return self._generate_basic_test(requirement)
        
        try:
            logger.info(f"使用 {provider_name} 基于代码分析生成测试用例...")
            tests_code = await provider.generate_code(
                requirement=test_prompt,
                language="python",
                extra_directives="生成完整的pytest测试代码，包含导入语句"
            )
            
            # 验证和修复测试代码
            tests_code = self._validate_and_fix_tests(tests_code, analysis)
            
            logger.info(f"✅ 智能测试用例生成完成")
            return tests_code
            
        except Exception as e:
            logger.error(f"❌ 智能测试生成失败: {e}")
            return self._generate_basic_test(requirement)
    
    def _build_role_based_test_prompt(self, code: str, analysis: Dict[str, Any], 
                                     requirement: str, role: str, role_prompt: Optional[str] = None) -> str:
        """构建基于角色的测试生成提示"""
        # 获取角色特定的测试策略
        role_strategy = self._get_role_testing_strategy(role)
        
        # 基础提示
        base_prompt = self._build_test_prompt(code, analysis, requirement)
        
        # 添加角色特定的测试要求
        role_specific_prompt = f"""
        
**角色测试策略 - {role_strategy['name']}：**
{role_strategy['description']}

**角色特定测试要求：**
{role_strategy['test_requirements']}

**测试重点：**
{role_strategy['focus_areas']}
"""
        
        if role_prompt:
            role_specific_prompt += f"""
            
**角色指导原则：**
{role_prompt}
"""
        
        return base_prompt + role_specific_prompt
    
    def _get_role_testing_strategy(self, role: str) -> Dict[str, str]:
        """获取角色特定的测试策略"""
        strategies = {
            "developer": {
                "name": "开发人员测试策略",
                "description": "注重功能完整性和代码质量验证",
                "test_requirements": """
- 全面的功能测试覆盖
- 详细的边界条件测试
- 基本的异常处理测试
- 代码路径覆盖测试""",
                "focus_areas": """
- 确保所有功能按预期工作
- 验证输入输出的正确性
- 测试常见的使用场景
- 基础性能验证"""
            },
            "software_engineer": {
                "name": "软件工程师测试策略", 
                "description": "强调系统架构和工程质量的测试",
                "test_requirements": """
- 模块化测试设计
- 集成测试用例
- 接口契约测试
- 系统边界测试
- 依赖关系测试""",
                "focus_areas": """
- 模块间的交互测试
- 系统架构的健壮性
- 可扩展性验证
- 错误传播和处理
- 资源管理测试"""
            },
            "system_analyst": {
                "name": "系统分析师测试策略",
                "description": "深度业务逻辑和需求符合性测试",
                "test_requirements": """
- 业务需求验证测试
- 用户场景测试
- 数据流测试
- 业务规则验证
- 需求追溯测试""",
                "focus_areas": """
- 业务逻辑的正确性
- 需求的完整实现
- 用户体验验证
- 数据处理准确性
- 业务流程完整性"""
            },
            "senior_evaluator": {
                "name": "高级评测专家测试策略",
                "description": "全面的质量评估和性能测试",
                "test_requirements": """
- 全面的质量指标测试
- 性能基准测试
- 安全性测试
- 可靠性测试
- 压力测试和负载测试
- 代码质量度量测试""",
                "focus_areas": """
- 性能瓶颈识别
- 安全漏洞检测
- 内存和资源使用优化
- 并发和多线程安全
- 代码复杂度分析
- 可维护性评估"""
            },
            "software_analyst": {
                "name": "软件分析人员测试策略",
                "description": "深入的代码分析和质量保证测试",
                "test_requirements": """
- 静态代码分析测试
- 代码覆盖率测试
- 复杂度分析测试
- 潜在缺陷检测测试
- 代码规范符合性测试
- 技术债务评估测试""",
                "focus_areas": """
- 代码质量度量
- 潜在问题识别
- 代码可读性验证
- 最佳实践符合性
- 重构建议验证
- 代码异味检测"""
            }
        }
        
        return strategies.get(role, strategies["developer"])
    
    def _build_test_prompt(self, code: str, analysis: Dict[str, Any], requirement: str) -> str:
        """构建测试生成提示"""
        main_func = analysis.get("main_function")
        
        prompt = f"""请为以下Python代码生成完整的pytest测试用例：

**原始需求：**
{requirement}

**待测试的代码：**
```python
{code}
```

**代码分析结果：**
- 主函数：{main_func['name'] if main_func else '未找到solve函数'}
"""

        if main_func:
            params = main_func.get("parameters", [])
            return_type = main_func.get("return_type", "unknown")
            
            prompt += f"""- 函数参数：{', '.join([f"{p['name']}({p['type']})" for p in params]) if params else '无参数'}
- 返回类型：{return_type}
- 函数复杂度：{analysis.get('complexity', 'unknown')}
- 包含循环：{'是' if main_func.get('has_loops') else '否'}
- 包含条件判断：{'是' if main_func.get('has_conditions') else '否'}"""

        prompt += f"""

**测试要求：**
1. 生成完整的pytest测试文件，包含所有必要的import语句
2. 针对主函数 `{main_func['name'] if main_func else 'solve'}` 生成以下测试："""

        if main_func and main_func.get("parameters"):
            prompt += """
   - 正常情况测试（典型输入）
   - 边界值测试（最小值、最大值、空值等）
   - 异常情况测试（无效输入、类型错误等）"""
        else:
            prompt += """
   - 基本功能测试
   - 返回值验证测试"""

        if analysis.get("complexity") == "complex":
            prompt += """
   - 复杂逻辑分支测试
   - 性能测试（如果需要）"""

        prompt += """
3. 每个测试函数都要有清晰的命名和文档说明
4. 使用断言验证预期结果
5. 确保测试代码可以直接运行

**输出格式：**
只输出Python代码，不要包含markdown标记。代码应该能够直接保存为.py文件并运行。
"""
        
        return prompt
    
    def _validate_and_fix_tests(self, tests_code: str, analysis: Dict[str, Any]) -> str:
        """验证和修复测试代码"""
        # 清理markdown标记
        tests_code = re.sub(r'```python\s*', '', tests_code)
        tests_code = re.sub(r'```\s*$', '', tests_code)
        tests_code = tests_code.strip()
        
        # 确保有pytest导入
        if "import pytest" not in tests_code:
            tests_code = "import pytest\n" + tests_code
        
        # 确保有主函数导入（假设代码在某个模块中）
        main_func = analysis.get("main_function")
        if main_func and f"from {main_func['name']}" not in tests_code:
            # 添加导入说明注释
            import_comment = f"# 注意：实际使用时请根据代码文件位置修改导入语句\n# from your_module import {main_func['name']}\n\n"
            tests_code = import_comment + tests_code
        
        return tests_code
    
    def _generate_basic_test(self, requirement: str) -> str:
        """生成基础测试用例（当代码分析失败时的后备方案）"""
        return f"""# 基础测试用例 - 代码分析失败时的后备方案
import pytest

# 注意：请根据实际代码修改导入语句
# from your_module import solve

def test_basic_functionality():
    \"\"\"测试基本功能
    
    原始需求：{requirement}
    \"\"\"
    # TODO: 请根据实际代码实现测试
    assert True  # 占位符，请替换为实际测试逻辑

def test_edge_cases():
    \"\"\"测试边界情况\"\"\"
    # TODO: 添加边界情况测试
    pass

def test_error_handling():
    \"\"\"测试错误处理\"\"\"
    # TODO: 添加异常情况测试
    pass

# 提示：这是一个基础模板，请根据生成的代码具体实现测试逻辑
"""

    async def generate_multiple_test_strategies(self, code: str, requirement: str) -> List[Dict[str, str]]:
        """
        生成多种测试策略
        
        Args:
            code: 生成的代码
            requirement: 原始需求
            
        Returns:
            多种测试策略的列表
        """
        analysis = self.analyzer.analyze_code(code)
        strategies = []
        
        # 策略1：功能测试
        functional_prompt = self._build_functional_test_prompt(code, analysis, requirement)
        
        # 策略2：边界测试
        boundary_prompt = self._build_boundary_test_prompt(code, analysis, requirement)
        
        # 策略3：性能测试（如果适用）
        if analysis.get("complexity") in ["moderate", "complex"]:
            performance_prompt = self._build_performance_test_prompt(code, analysis, requirement)
            strategies.append({"type": "performance", "prompt": performance_prompt})
        
        strategies.extend([
            {"type": "functional", "prompt": functional_prompt},
            {"type": "boundary", "prompt": boundary_prompt}
        ])
        
        return strategies
    
    def _build_functional_test_prompt(self, code: str, analysis: Dict[str, Any], requirement: str) -> str:
        """构建功能测试提示"""
        return f"""专注于功能正确性的测试用例：

代码：
{code}

需求：{requirement}

请生成验证核心功能是否正确实现的pytest测试用例。"""
    
    def _build_boundary_test_prompt(self, code: str, analysis: Dict[str, Any], requirement: str) -> str:
        """构建边界测试提示"""
        return f"""专注于边界条件的测试用例：

代码：
{code}

需求：{requirement}

请生成测试边界条件、极值、空值等情况的pytest测试用例。"""
    
    def _build_performance_test_prompt(self, code: str, analysis: Dict[str, Any], requirement: str) -> str:
        """构建性能测试提示"""
        return f"""专注于性能验证的测试用例：

代码：
{code}

需求：{requirement}

请生成验证算法效率、时间复杂度等的pytest测试用例。"""
