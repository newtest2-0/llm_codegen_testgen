#!/usr/bin/env python3
"""
LLM代码生成平台 - 环境设置脚本
用于首次安装和环境配置
"""
import os
import sys
import json
import subprocess
import platform
from pathlib import Path

def print_colored(message, color="white"):
    """打印彩色消息"""
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

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60 + "\n")

def check_system_requirements():
    """检查系统要求"""
    print_colored("🔍 检查系统要求...", "yellow")
    
    # 检查Python版本
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored("❌ Python版本不符合要求", "red")
        print_colored(f"   需要：Python 3.8+", "yellow")
        print_colored(f"   当前：Python {version.major}.{version.minor}.{version.micro}", "yellow")
        return False
    
    print_colored(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}", "green")
    
    # 检查操作系统
    system = platform.system()
    print_colored(f"✅ 操作系统: {system} {platform.release()}", "green")
    
    return True

def create_virtual_environment():
    """创建虚拟环境"""
    print_colored("📦 设置Python虚拟环境...", "yellow")
    
    venv_path = Path(".venv")
    if venv_path.exists():
        print_colored("ℹ️  虚拟环境已存在，跳过创建", "blue")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print_colored("✅ 虚拟环境创建成功", "green")
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ 虚拟环境创建失败: {e}", "red")
        return False

def install_dependencies():
    """安装项目依赖"""
    print_colored("📦 安装项目依赖...", "yellow")
    
    # 获取虚拟环境中的pip路径
    system = platform.system().lower()
    if system == "windows":
        pip_path = Path(".venv") / "Scripts" / "pip.exe"
    else:
        pip_path = Path(".venv") / "bin" / "pip"
    
    if not pip_path.exists():
        print_colored("❌ 虚拟环境pip未找到", "red")
        return False
    
    try:
        # 升级pip
        print_colored("  升级pip...", "blue")
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        # 安装项目依赖
        print_colored("  安装requirements.txt...", "blue")
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        
        print_colored("✅ 依赖安装完成", "green")
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ 依赖安装失败: {e}", "red")
        return False

def setup_configuration():
    """设置配置文件"""
    print_colored("🔧 设置配置文件...", "yellow")
    
    config_path = Path("config.json")
    
    if config_path.exists():
        print_colored("ℹ️  配置文件已存在", "blue")
        
        # 验证配置文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            providers = config.get('providers', [])
            print_colored(f"✅ 当前配置包含 {len(providers)} 个AI提供者", "green")
            
            # 检查是否有配置的API密钥
            configured_count = 0
            for provider in providers:
                env_var = provider.get('api_key_env')
                if env_var and os.getenv(env_var):
                    configured_count += 1
            
            if configured_count > 0:
                print_colored(f"✅ 已配置 {configured_count} 个提供者的API密钥", "green")
            else:
                print_colored("⚠️  尚未配置任何API密钥", "yellow")
                print_setup_instructions()
            
            return True
            
        except Exception as e:
            print_colored(f"❌ 配置文件格式错误: {e}", "red")
            return False
    else:
        print_colored("ℹ️  配置文件不存在，将使用默认配置", "blue")
        print_setup_instructions()
        return True

def print_setup_instructions():
    """打印设置说明"""
    print_colored("\n📝 配置说明:", "cyan")
    print_colored("1. 编辑 config.json 文件配置AI提供者", "white")
    print_colored("2. 设置环境变量配置API密钥:", "white")
    
    providers = [
        ("OpenAI", "OPENAI_API_KEY", "OPENAI_BASE_URL"),
        ("DeepSeek", "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL"),
        ("Anthropic Claude", "ANTHROPIC_API_KEY", ""),
        ("Google Gemini", "GOOGLE_API_KEY", ""),
        ("通义千问", "QWEN_API_KEY", "QWEN_BASE_URL"),
        ("百川", "BAICHUAN_API_KEY", "BAICHUAN_BASE_URL"),
        ("智谱GLM", "CHATGLM_API_KEY", "CHATGLM_BASE_URL"),
        ("Ollama本地", "OLLAMA_API_KEY", "OLLAMA_BASE_URL"),
    ]
    
    for name, key_env, url_env in providers:
        print_colored(f"   {name}: {key_env}", "blue")
        if url_env:
            print_colored(f"            {url_env}", "blue")

def create_env_example():
    """创建环境变量示例文件"""
    print_colored("📄 创建.env.example文件...", "yellow")
    
    env_example = """# LLM代码生成平台 - 环境变量配置示例
# 复制此文件为.env并配置您的API密钥

# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Anthropic Claude配置
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Gemini配置
GOOGLE_API_KEY=your_google_api_key_here

# 通义千问配置
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 百川配置
BAICHUAN_API_KEY=your_baichuan_api_key_here
BAICHUAN_BASE_URL=https://api.baichuan-ai.com/v1

# 智谱GLM配置
CHATGLM_API_KEY=your_chatglm_api_key_here
CHATGLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# Ollama本地配置（如果使用本地模型）
OLLAMA_API_KEY=your_ollama_api_key_here
OLLAMA_BASE_URL=http://localhost:11434/v1
"""
    
    try:
        with open(".env.example", "w", encoding="utf-8") as f:
            f.write(env_example)
        print_colored("✅ .env.example文件创建成功", "green")
        return True
    except Exception as e:
        print_colored(f"❌ .env.example文件创建失败: {e}", "red")
        return False

def run_tests():
    """运行基础测试"""
    print_colored("🧪 运行基础测试...", "yellow")
    
    system = platform.system().lower()
    if system == "windows":
        python_path = Path(".venv") / "Scripts" / "python.exe"
    else:
        python_path = Path(".venv") / "bin" / "python"
    
    if not python_path.exists():
        print_colored("❌ 虚拟环境Python解释器未找到", "red")
        return False
    
    try:
        # 测试导入核心模块
        test_script = """
import sys
sys.path.append('backend')

try:
    from core.config import config
    from core.providers import ProviderManager
    print("✅ 核心模块导入成功")
except Exception as e:
    print(f"❌ 核心模块导入失败: {e}")
    sys.exit(1)
"""
        
        result = subprocess.run(
            [str(python_path), "-c", test_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_colored("✅ 基础测试通过", "green")
            return True
        else:
            print_colored(f"❌ 基础测试失败: {result.stderr}", "red")
            return False
            
    except Exception as e:
        print_colored(f"❌ 测试执行失败: {e}", "red")
        return False

def main():
    """主函数"""
    print_header("🎯 LLM代码生成平台 - 环境设置")
    
    try:
        # 检查系统要求
        if not check_system_requirements():
            return 1
        
        # 创建虚拟环境
        if not create_virtual_environment():
            return 1
        
        # 安装依赖
        if not install_dependencies():
            return 1
        
        # 设置配置
        if not setup_configuration():
            return 1
        
        # 创建环境变量示例
        create_env_example()
        
        # 运行基础测试
        if not run_tests():
            print_colored("⚠️  基础测试失败，但安装可能仍然有效", "yellow")
        
        print_header("🎉 环境设置完成")
        print_colored("接下来您可以:", "cyan")
        print_colored("1. 配置API密钥（参考.env.example）", "white")
        print_colored("2. 运行启动脚本:", "white")
        print_colored("   - Windows: run.bat 或 run.ps1", "blue")
        print_colored("   - 跨平台: python run.py", "blue")
        print_colored("   - 原始脚本: python scripts/start.py", "blue")
        
        return 0
        
    except Exception as e:
        print_colored(f"💥 环境设置过程中发生错误: {e}", "red")
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    # 在Windows上等待用户按键
    if platform.system().lower() == "windows":
        input("\n按回车键退出...")
    
    sys.exit(exit_code)
