"""
综合代码质量评估模块
整合多种代码分析工具和评估指标
"""
import ast
import re
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os

logger = logging.getLogger(__name__)

@dataclass
class CodeQualityMetrics:
    """代码质量指标"""
    # 基础指标
    lines_of_code: int = 0
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 0.0
    
    # 语法和结构
    syntax_errors: List[str] = None
    ast_quality_score: float = 0.0
    
    # 代码风格
    pep8_violations: List[Dict[str, Any]] = None
    style_score: float = 0.0
    
    # 安全性
    security_issues: List[Dict[str, Any]] = None
    security_score: float = 0.0
    
    # 文档质量
    docstring_coverage: float = 0.0
    comment_ratio: float = 0.0
    
    # 代码复杂度细分
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    function_length_avg: float = 0.0
    
    # 潜在问题
    code_smells: List[str] = None
    duplicate_code: List[Dict[str, Any]] = None
    
    # 综合评分
    overall_score: float = 0.0
    
    def __post_init__(self):
        if self.syntax_errors is None:
            self.syntax_errors = []
        if self.pep8_violations is None:
            self.pep8_violations = []
        if self.security_issues is None:
            self.security_issues = []
        if self.code_smells is None:
            self.code_smells = []
        if self.duplicate_code is None:
            self.duplicate_code = []

class CodeComplexityAnalyzer:
    """代码复杂度分析器"""
    
    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """分析代码复杂度"""
        try:
            tree = ast.parse(code)
            
            complexity_data = {
                "cyclomatic_complexity": self._calculate_cyclomatic_complexity(tree),
                "cognitive_complexity": self._calculate_cognitive_complexity(tree),
                "nesting_depth": self._calculate_max_nesting_depth(tree),
                "function_lengths": self._analyze_function_lengths(tree),
                "class_complexity": self._analyze_class_complexity(tree)
            }
            
            return complexity_data
            
        except SyntaxError as e:
            logger.warning(f"语法错误，无法分析复杂度: {e}")
            return {"error": str(e)}
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """计算认知复杂度"""
        complexity = 0
        nesting_level = 0
        
        def visit_node(node, level=0):
            nonlocal complexity
            
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += (1 + level)
            elif isinstance(node, ast.Try):
                complexity += (1 + level)
            elif isinstance(node, ast.BoolOp):
                complexity += 1
            
            # 递归访问子节点，增加嵌套层级
            for child in ast.iter_child_nodes(node):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                    visit_node(child, level + 1)
                else:
                    visit_node(child, level)
        
        visit_node(tree)
        return complexity
    
    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """计算最大嵌套深度"""
        max_depth = 0
        
        def calculate_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                    calculate_depth(child, current_depth + 1)
                else:
                    calculate_depth(child, current_depth)
        
        calculate_depth(tree)
        return max_depth
    
    def _analyze_function_lengths(self, tree: ast.AST) -> Dict[str, Any]:
        """分析函数长度"""
        function_lengths = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 计算函数的行数
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    length = node.end_lineno - node.lineno + 1
                else:
                    length = len(node.body)
                
                function_lengths.append({
                    "name": node.name,
                    "length": length
                })
        
        if function_lengths:
            lengths = [f["length"] for f in function_lengths]
            return {
                "functions": function_lengths,
                "average_length": sum(lengths) / len(lengths),
                "max_length": max(lengths),
                "min_length": min(lengths)
            }
        
        return {"functions": [], "average_length": 0, "max_length": 0, "min_length": 0}
    
    def _analyze_class_complexity(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """分析类复杂度"""
        class_info = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                class_info.append({
                    "name": node.name,
                    "method_count": len(methods),
                    "methods": [m.name for m in methods]
                })
        
        return class_info

class CodeStyleAnalyzer:
    """代码风格分析器"""
    
    def analyze_style(self, code: str) -> Dict[str, Any]:
        """分析代码风格"""
        violations = []
        
        # 基本的PEP8检查
        violations.extend(self._check_line_length(code))
        violations.extend(self._check_indentation(code))
        violations.extend(self._check_naming_conventions(code))
        violations.extend(self._check_imports(code))
        violations.extend(self._check_whitespace(code))
        
        # 计算风格评分
        total_lines = len(code.split('\n'))
        violation_count = len(violations)
        style_score = max(0, 100 - (violation_count * 100 / max(total_lines, 1)))
        
        return {
            "violations": violations,
            "violation_count": violation_count,
            "style_score": style_score / 100.0,
            "total_lines": total_lines
        }
    
    def _check_line_length(self, code: str) -> List[Dict[str, Any]]:
        """检查行长度"""
        violations = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            if len(line) > 79:  # PEP8标准
                violations.append({
                    "type": "line_too_long",
                    "line": i,
                    "message": f"Line too long ({len(line)} > 79 characters)",
                    "severity": "warning"
                })
        
        return violations
    
    def _check_indentation(self, code: str) -> List[Dict[str, Any]]:
        """检查缩进"""
        violations = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            if line.strip() and line.startswith('\t'):
                violations.append({
                    "type": "tab_indentation",
                    "line": i,
                    "message": "Use spaces instead of tabs for indentation",
                    "severity": "error"
                })
        
        return violations
    
    def _check_naming_conventions(self, code: str) -> List[Dict[str, Any]]:
        """检查命名约定"""
        violations = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                        violations.append({
                            "type": "function_naming",
                            "line": getattr(node, 'lineno', 0),
                            "message": f"Function name '{node.name}' should be lowercase with underscores",
                            "severity": "warning"
                        })
                
                elif isinstance(node, ast.ClassDef):
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                        violations.append({
                            "type": "class_naming",
                            "line": getattr(node, 'lineno', 0),
                            "message": f"Class name '{node.name}' should use CapWords convention",
                            "severity": "warning"
                        })
        
        except SyntaxError:
            pass  # 语法错误会在其他地方处理
        
        return violations
    
    def _check_imports(self, code: str) -> List[Dict[str, Any]]:
        """检查导入语句"""
        violations = []
        lines = code.split('\n')
        
        import_lines = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                import_lines.append((i, stripped))
        
        # 检查导入顺序（标准库 -> 第三方 -> 本地）
        # 这里简化处理，只检查是否有空行分隔
        
        return violations
    
    def _check_whitespace(self, code: str) -> List[Dict[str, Any]]:
        """检查空白字符"""
        violations = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 检查行尾空白
            if line.rstrip() != line:
                violations.append({
                    "type": "trailing_whitespace",
                    "line": i,
                    "message": "Trailing whitespace",
                    "severity": "info"
                })
        
        return violations

class SecurityAnalyzer:
    """安全性分析器"""
    
    def analyze_security(self, code: str) -> Dict[str, Any]:
        """分析安全问题"""
        issues = []
        
        # 检查常见安全问题
        issues.extend(self._check_dangerous_functions(code))
        issues.extend(self._check_sql_injection(code))
        issues.extend(self._check_command_injection(code))
        issues.extend(self._check_hardcoded_secrets(code))
        
        # 计算安全评分
        critical_count = len([i for i in issues if i.get("severity") == "critical"])
        high_count = len([i for i in issues if i.get("severity") == "high"])
        medium_count = len([i for i in issues if i.get("severity") == "medium"])
        
        # 安全评分计算
        penalty = critical_count * 30 + high_count * 20 + medium_count * 10
        security_score = max(0, 100 - penalty) / 100.0
        
        return {
            "issues": issues,
            "issue_count": len(issues),
            "security_score": security_score,
            "risk_level": self._calculate_risk_level(critical_count, high_count, medium_count)
        }
    
    def _check_dangerous_functions(self, code: str) -> List[Dict[str, Any]]:
        """检查危险函数"""
        issues = []
        dangerous_patterns = [
            (r'\beval\s*\(', "Use of eval() is dangerous", "critical"),
            (r'\bexec\s*\(', "Use of exec() is dangerous", "critical"),
            (r'\b__import__\s*\(', "Dynamic imports can be dangerous", "medium"),
            (r'\binput\s*\([^)]*\)', "Raw input() can be dangerous in Python 2", "medium"),
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message, severity in dangerous_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "type": "dangerous_function",
                        "line": i,
                        "message": message,
                        "severity": severity,
                        "code": line.strip()
                    })
        
        return issues
    
    def _check_sql_injection(self, code: str) -> List[Dict[str, Any]]:
        """检查SQL注入风险"""
        issues = []
        
        # 检查字符串格式化的SQL查询
        sql_patterns = [
            (r'.*\.execute\s*\(\s*["\'].*%.*["\']', "Potential SQL injection via string formatting"),
            (r'.*\.execute\s*\(\s*.*\.format\s*\(', "Potential SQL injection via .format()"),
            (r'.*\.execute\s*\(\s*f["\']', "Potential SQL injection via f-string"),
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "type": "sql_injection",
                        "line": i,
                        "message": message,
                        "severity": "high",
                        "code": line.strip()
                    })
        
        return issues
    
    def _check_command_injection(self, code: str) -> List[Dict[str, Any]]:
        """检查命令注入风险"""
        issues = []
        
        command_patterns = [
            (r'\bos\.system\s*\(', "os.system() can be vulnerable to command injection"),
            (r'\bsubprocess\.call\s*\([^)]*shell\s*=\s*True', "subprocess with shell=True is dangerous"),
            (r'\bos\.popen\s*\(', "os.popen() can be vulnerable"),
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in command_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "type": "command_injection",
                        "line": i,
                        "message": message,
                        "severity": "high",
                        "code": line.strip()
                    })
        
        return issues
    
    def _check_hardcoded_secrets(self, code: str) -> List[Dict[str, Any]]:
        """检查硬编码的密钥"""
        issues = []
        
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password detected"),
            (r'api_key\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded secret detected"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded token detected"),
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "type": "hardcoded_secret",
                        "line": i,
                        "message": message,
                        "severity": "critical",
                        "code": re.sub(r'["\'][^"\']*["\']', '"***REDACTED***"', line.strip())
                    })
        
        return issues
    
    def _calculate_risk_level(self, critical: int, high: int, medium: int) -> str:
        """计算风险等级"""
        if critical > 0:
            return "critical"
        elif high > 2:
            return "high"
        elif high > 0 or medium > 5:
            return "medium"
        elif medium > 0:
            return "low"
        else:
            return "minimal"

class ComprehensiveCodeEvaluator:
    """综合代码评估器"""
    
    def __init__(self):
        self.complexity_analyzer = CodeComplexityAnalyzer()
        self.style_analyzer = CodeStyleAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
    
    def evaluate_code(self, code: str, requirement: Optional[str] = None) -> CodeQualityMetrics:
        """
        综合评估代码质量
        
        Args:
            code: 要评估的代码
            requirement: 原始需求（可选）
            
        Returns:
            代码质量指标
        """
        logger.info("开始综合代码质量评估...")
        
        metrics = CodeQualityMetrics()
        
        # 基础指标
        metrics.lines_of_code = len([line for line in code.split('\n') if line.strip()])
        
        # 语法检查
        try:
            ast.parse(code)
            metrics.ast_quality_score = 1.0
        except SyntaxError as e:
            metrics.syntax_errors.append(str(e))
            metrics.ast_quality_score = 0.0
        
        # 复杂度分析
        complexity_data = self.complexity_analyzer.analyze_complexity(code)
        if "error" not in complexity_data:
            metrics.cyclomatic_complexity = complexity_data.get("cyclomatic_complexity", 0)
            metrics.cognitive_complexity = complexity_data.get("cognitive_complexity", 0)
            metrics.nesting_depth = complexity_data.get("nesting_depth", 0)
            
            func_data = complexity_data.get("function_lengths", {})
            metrics.function_length_avg = func_data.get("average_length", 0.0)
        
        # 风格分析
        style_data = self.style_analyzer.analyze_style(code)
        metrics.pep8_violations = style_data.get("violations", [])
        metrics.style_score = style_data.get("style_score", 0.0)
        
        # 安全性分析
        security_data = self.security_analyzer.analyze_security(code)
        metrics.security_issues = security_data.get("issues", [])
        metrics.security_score = security_data.get("security_score", 0.0)
        
        # 文档质量分析
        metrics.docstring_coverage = self._calculate_docstring_coverage(code)
        metrics.comment_ratio = self._calculate_comment_ratio(code)
        
        # 代码异味检测
        metrics.code_smells = self._detect_code_smells(code)
        
        # 可维护性指数计算
        metrics.maintainability_index = self._calculate_maintainability_index(metrics)
        
        # 综合评分计算
        metrics.overall_score = self._calculate_overall_score(metrics)
        
        logger.info(f"代码质量评估完成，综合得分: {metrics.overall_score:.3f}")
        
        return metrics
    
    def _calculate_docstring_coverage(self, code: str) -> float:
        """计算文档字符串覆盖率"""
        try:
            tree = ast.parse(code)
            
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            total_items = len(functions) + len(classes)
            if total_items == 0:
                return 1.0
            
            documented_items = 0
            
            for item in functions + classes:
                if (item.body and 
                    isinstance(item.body[0], ast.Expr) and 
                    isinstance(item.body[0].value, ast.Constant) and 
                    isinstance(item.body[0].value.value, str)):
                    documented_items += 1
            
            return documented_items / total_items
            
        except SyntaxError:
            return 0.0
    
    def _calculate_comment_ratio(self, code: str) -> float:
        """计算注释比例"""
        lines = code.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        
        return comment_lines / max(total_lines, 1)
    
    def _detect_code_smells(self, code: str) -> List[str]:
        """检测代码异味"""
        smells = []
        
        try:
            tree = ast.parse(code)
            
            # 检测长函数
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                        length = node.end_lineno - node.lineno + 1
                        if length > 50:
                            smells.append(f"Long function: {node.name} ({length} lines)")
                    
                    # 检测参数过多
                    if len(node.args.args) > 6:
                        smells.append(f"Too many parameters: {node.name} ({len(node.args.args)} params)")
            
            # 检测深度嵌套
            if self.complexity_analyzer._calculate_max_nesting_depth(tree) > 4:
                smells.append("Deep nesting detected (>4 levels)")
            
            # 检测重复代码（简化版）
            lines = code.split('\n')
            line_counts = {}
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    line_counts[stripped] = line_counts.get(stripped, 0) + 1
            
            duplicates = [(line, count) for line, count in line_counts.items() if count > 2 and len(line) > 20]
            if duplicates:
                smells.append(f"Potential code duplication detected ({len(duplicates)} patterns)")
        
        except SyntaxError:
            pass
        
        return smells
    
    def _calculate_maintainability_index(self, metrics: CodeQualityMetrics) -> float:
        """计算可维护性指数"""
        # 基于多个因素的加权平均
        factors = [
            (metrics.ast_quality_score, 0.2),  # 语法质量
            (metrics.style_score, 0.15),       # 代码风格
            (metrics.security_score, 0.15),    # 安全性
            (metrics.docstring_coverage, 0.1), # 文档覆盖率
            (min(1.0, metrics.comment_ratio * 10), 0.1),  # 注释比例
        ]
        
        # 复杂度惩罚
        complexity_penalty = min(1.0, metrics.cyclomatic_complexity / 20.0)
        nesting_penalty = min(1.0, metrics.nesting_depth / 8.0)
        
        weighted_score = sum(score * weight for score, weight in factors)
        complexity_factor = 1.0 - (complexity_penalty * 0.15 + nesting_penalty * 0.15)
        
        return max(0.0, min(1.0, weighted_score * complexity_factor))
    
    def _calculate_overall_score(self, metrics: CodeQualityMetrics) -> float:
        """计算综合评分"""
        # 权重配置
        weights = {
            "functionality": 0.30,    # 功能性（语法正确性）
            "maintainability": 0.25,  # 可维护性
            "style": 0.15,           # 代码风格
            "security": 0.15,        # 安全性
            "documentation": 0.10,   # 文档质量
            "complexity": 0.05       # 复杂度
        }
        
        # 各维度得分
        functionality_score = metrics.ast_quality_score
        maintainability_score = metrics.maintainability_index
        style_score = metrics.style_score
        security_score = metrics.security_score
        documentation_score = (metrics.docstring_coverage + min(1.0, metrics.comment_ratio * 5)) / 2
        
        # 复杂度得分（复杂度越高得分越低）
        complexity_score = max(0.0, 1.0 - (metrics.cyclomatic_complexity - 1) / 20.0)
        
        # 加权计算
        overall_score = (
            functionality_score * weights["functionality"] +
            maintainability_score * weights["maintainability"] +
            style_score * weights["style"] +
            security_score * weights["security"] +
            documentation_score * weights["documentation"] +
            complexity_score * weights["complexity"]
        )
        
        return max(0.0, min(1.0, overall_score))
