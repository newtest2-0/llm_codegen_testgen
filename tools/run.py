#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM代码生成平台 - 简化一键启动脚本
跨平台支持：Windows、macOS、Linux
"""
import os
import sys
import subprocess
import platform
from pathlib import Path
import io

# 设置Windows控制台UTF-8编码
if platform.system().lower() == 'windows':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60 + "\n")

def print_colored(message, color="white"):
    """打印彩色消息（简化版）"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m", 
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    color_code = colors.get(color, colors["white"])
    reset_code = colors["reset"]
    print(f"{color_code}{message}{reset_code}")

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored("[ERROR] 需要Python 3.8或更高版本", "red")
        print_colored(f"   当前版本：{version.major}.{version.minor}.{version.micro}", "yellow")
        return False
    
    print_colored(f"[OK] Python版本检查通过：{version.major}.{version.minor}.{version.micro}", "green")
    return True

def check_project_structure():
    """检查项目结构"""
    print_colored("[Check] 检查项目结构...", "yellow")
    
    required_paths = ["backend", "scripts", "requirements.txt"]
    for path in required_paths:
        if not Path(path).exists():
            print_colored(f"[ERROR] 未找到必需的文件或目录: {path}", "red")
            return False
    
    print_colored("[OK] 项目结构检查通过", "green")
    return True

def setup_virtual_environment():
    """设置虚拟环境"""
    venv_path = Path(".venv")
    
    if not venv_path.exists():
        print_colored("[Setup] 创建虚拟环境...", "yellow")
        try:
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            print_colored("[OK] 虚拟环境创建成功", "green")
        except subprocess.CalledProcessError:
            print_colored("[ERROR] 虚拟环境创建失败", "red")
            return False
    
    # 获取虚拟环境中的Python路径
    system = platform.system().lower()
    if system == "windows":
        python_path = venv_path / "Scripts" / "python.exe"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        python_path = venv_path / "bin" / "python"
        pip_path = venv_path / "bin" / "pip"
    
    if not python_path.exists():
        print_colored("[ERROR] 虚拟环境Python解释器未找到", "red")
        return False
    
    return str(python_path), str(pip_path)

def install_dependencies(pip_path):
    """安装依赖"""
    print_colored("[Setup] 安装Python依赖...", "yellow")
    
    try:
        # 升级pip
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        
        # 安装项目依赖
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        
        print_colored("[OK] 依赖安装完成", "green")
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"[ERROR] 依赖安装失败: {e}", "red")
        return False

def check_configuration():
    """检查配置文件"""
    print_colored("[Check] 检查配置文件...", "yellow")
    
    config_path = Path("config.json")
    if not config_path.exists():
        print_colored("[ERROR] 未找到config.json配置文件", "red")
        print_colored("[INFO] 请参考README.md配置API密钥", "yellow")
        return False
    
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        provider_count = len(config.get('providers', []))
        print_colored(f"[OK] 配置文件有效，包含 {provider_count} 个AI提供者", "green")
        return True
    except Exception as e:
        print_colored(f"[ERROR] 配置文件格式错误: {e}", "red")
        return False

def start_services(python_path):
    """启动服务"""
    print_header("[Start] 启动服务")
    
    print_colored("[Info] 服务地址:", "cyan")
    print_colored("  [Frontend] 前端界面: http://localhost:8080", "blue")
    print_colored("  [Backend]  后端API: http://localhost:8000", "blue") 
    print_colored("  [Docs]     API文档: http://localhost:8000/docs", "blue")
    print()
    print_colored("[Info] 按 Ctrl+C 停止服务", "yellow")
    print()
    
    try:
        subprocess.run([python_path, "scripts/start.py"], check=True)
    except subprocess.CalledProcessError as e:
        print_colored(f"[ERROR] 服务启动失败: {e}", "red")
        return False
    except KeyboardInterrupt:
        print_colored("\n[Info] 用户中断服务", "yellow")
        return True
    
    return True

def main():
    """主函数"""
    try:
        print_header("Professional Code Development Platform - 一键启动器")
        
        # 检查Python版本
        if not check_python_version():
            return 1
        
        # 检查项目结构
        if not check_project_structure():
            return 1
        
        # 设置虚拟环境
        print_colored("[Setup] 设置虚拟环境...", "yellow")
        env_result = setup_virtual_environment()
        if not env_result:
            return 1
        
        python_path, pip_path = env_result
        print_colored("[OK] 虚拟环境准备就绪", "green")
        
        # 安装依赖
        if not install_dependencies(pip_path):
            return 1
        
        # 检查配置
        if not check_configuration():
            return 1
        
        # 启动服务
        if not start_services(python_path):
            return 1
        
        print_colored("[Info] 启动器退出", "yellow")
        return 0
        
    except Exception as e:
        print_colored(f"[ERROR] 启动过程中发生错误: {e}", "red")
        print_colored("[Info] 请检查错误信息并重试", "yellow")
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    # 在Windows上等待用户按键
    if platform.system().lower() == "windows":
        input("\n按回车键退出...")
    
    sys.exit(exit_code)
