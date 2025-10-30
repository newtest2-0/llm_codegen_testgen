"""
测试执行器模块
用于运行生成的测试代码并收集测试结果
"""
import subprocess
import tempfile
import os
import logging
from typing import Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class TestExecutor:
    """测试执行器，用于运行测试代码并收集结果"""
    
    def __init__(self, timeout: int = 30):
        """
        初始化测试执行器
        
        Args:
            timeout: 测试执行超时时间（秒）
        """
        self.timeout = timeout
    
    def run_tests(self, code: str, tests_code: str) -> Dict[str, Any]:
        """
        运行测试代码并收集结果
        
        Args:
            code: 待测试的源代码
            tests_code: 测试代码
            
        Returns:
            测试结果字典，包含通过测试数、总测试数等信息
        """
        logger.info("开始执行测试...")
        
        try:
            # 创建临时目录来存放代码和测试文件
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 保存源代码到文件
                source_file = temp_path / "source.py"
                with open(source_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                # 保存测试代码到文件
                test_file = temp_path / "test_source.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(tests_code)
                
                # 运行测试
                passed_tests, total_tests, exit_code = self._execute_pytest(test_file)
                
                logger.info(f"测试执行完成: {passed_tests}/{total_tests} 通过")
                
                return {
                    "passed_tests": passed_tests,
                    "total_tests": total_tests,
                    "exit_code": exit_code,
                    "success": exit_code == 0
                }
                
        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            return {
                "passed_tests": 0,
                "total_tests": 0,
                "exit_code": -1,
                "success": False,
                "error": str(e)
            }
    
    def _execute_pytest(self, test_file: Path) -> Tuple[int, int, int]:
        """
        执行pytest命令并解析结果
        
        Args:
            test_file: 测试文件路径
            
        Returns:
            (通过测试数, 总测试数, 退出码)
        """
        try:
            # 构建pytest命令
            cmd = [
                "python", "-m", "pytest",
                str(test_file),
                "-v",
                "--tb=short"
            ]
            
            # 执行测试
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # 解析测试结果
            passed_tests, total_tests = self._parse_pytest_output(
                result.stdout, 
                result.stderr
            )
            
            return passed_tests, total_tests, result.returncode
            
        except subprocess.TimeoutExpired:
            logger.warning(f"测试执行超时 ({self.timeout}秒)")
            return 0, 0, -1
        except Exception as e:
            logger.error(f"执行pytest失败: {e}")
            return 0, 0, -1
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> Tuple[int, int]:
        """
        解析pytest输出，提取通过测试数和总测试数
        
        Args:
            stdout: 标准输出
            stderr: 标准错误输出
            
        Returns:
            (通过测试数, 总测试数)
        """
        passed_tests = 0
        total_tests = 0
        
        # 查找类似 "===== 3 passed in 0.12s =====" 的行
        lines = (stdout + stderr).split('\n')
        for line in lines:
            if "passed" in line and "failed" in line:
                # 格式如: "= 2 failed, 3 passed in 0.12s ="
                import re
                passed_match = re.search(r'(\d+)\s+passed', line)
                failed_match = re.search(r'(\d+)\s+failed', line)
                
                if passed_match:
                    passed_tests = int(passed_match.group(1))
                if failed_match:
                    failed_tests = int(failed_match.group(1))
                    total_tests = passed_tests + failed_tests
                break
            elif "passed" in line and "=" in line:
                # 格式如: "= 3 passed in 0.12s ="
                import re
                passed_match = re.search(r'(\d+)\s+passed', line)
                if passed_match:
                    passed_tests = int(passed_match.group(1))
                    total_tests = passed_tests
                break
        
        return passed_tests, total_tests