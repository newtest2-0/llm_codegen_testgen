#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Code Development Platform
智能代码生成平台 - 快速启动脚本（根目录简化版）
"""
import sys
import subprocess
from pathlib import Path
import platform
import io

# 设置Windows控制台UTF-8编码
if platform.system().lower() == 'windows':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def main():
    """快速启动主函数"""
    print("=" * 60)
    print("Professional Code Development Platform")
    print("智能代码生成平台 - 快速启动")
    print("=" * 60)
    
    # 调用tools目录中的详细启动脚本
    tools_script = Path("tools") / "run.py"
    
    if not tools_script.exists():
        print("❌ 错误：未找到tools/run.py启动脚本")
        print("请确保项目结构完整")
        return 1
    
    try:
        subprocess.run([sys.executable, str(tools_script)], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 用户中断启动")
        return 0

if __name__ == "__main__":
    sys.exit(main())
