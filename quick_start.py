#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Code Development Platform
快速启动脚本 - 无需虚拟环境，直接启动
"""
import sys
import subprocess
import time
from pathlib import Path
import platform
import io

# 设置Windows控制台UTF-8编码
if platform.system().lower() == 'windows':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

def main():
    """快速启动"""
    print("=" * 70)
    print("  Professional Code Development Platform")
    print("  UML Diagram-Driven Code Generation System")
    print("=" * 70)
    print()
    
    project_root = Path(__file__).parent
    
    # 检查后端目录
    if not (project_root / "backend").exists():
        print("[ERROR] 未找到backend目录，请确保项目结构完整")
        return 1
    
    backend_process = None
    frontend_process = None
    
    try:
        # 启动后端
        print("[1/2] 启动后端服务 (FastAPI on port 8000)...")
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", 
             "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=str(project_root / "backend")
        )
        time.sleep(3)
        print("[OK] 后端服务已启动")
        
        # 启动前端
        print("[2/2] 启动前端服务 (Static Server on port 8080)...")
        frontend_process = subprocess.Popen(
            [sys.executable, "start_server.py"],
            cwd=str(project_root / "web")
        )
        time.sleep(2)
        print("[OK] 前端服务已启动")
        
        print()
        print("=" * 70)
        print("  [SUCCESS] 服务启动完成！")
        print("=" * 70)
        print()
        print("  访问地址:")
        print("  --> 前端界面: http://localhost:8080")
        print("  --> 后端API:  http://localhost:8000")
        print("  --> API文档:  http://localhost:8000/docs")
        print()
        print("=" * 70)
        print("  功能亮点:")
        print("  - 5个专业开发文档模块")
        print("  - 5种UML图表类型支持")
        print("  - AI自动生成图表")
        print("  - 基于图表生成代码")
        print("  - LLM智能评阅系统")
        print("  - 完整工作流自动化")
        print("=" * 70)
        print()
        print("[INFO] 按 Ctrl+C 停止所有服务")
        print()
        
        # 等待用户中断
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("[INFO] 正在停止所有服务...")
        print("=" * 70)
        
    finally:
        # 停止后端
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
                print("[OK] 后端服务已停止")
            except subprocess.TimeoutExpired:
                backend_process.kill()
                print("[OK] 后端服务已强制停止")
        
        # 停止前端
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
                print("[OK] 前端服务已停止")
            except subprocess.TimeoutExpired:
                frontend_process.kill()
                print("[OK] 前端服务已强制停止")
        
        print()
        print("=" * 70)
        print("  [DONE] 所有服务已停止，感谢使用！")
        print("=" * 70)
        print()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as e:
        print(f"\n[ERROR] 启动失败: {e}")
        exit_code = 1
    
    # Windows上等待用户按键
    if platform.system().lower() == "windows":
        input("\n按回车键退出...")
    
    sys.exit(exit_code)

