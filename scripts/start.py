#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目启动脚本
"""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from threading import Thread
import platform
import io

# 设置Windows控制台UTF-8编码
if platform.system().lower() == 'windows':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.parent

def start_backend():
    """启动后端服务"""
    project_root = get_project_root()
    os.chdir(project_root)
    
    print("[Backend] 启动后端服务...")
    
    # 检查虚拟环境
    if sys.platform == "win32":
        python_path = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        python_path = project_root / ".venv" / "bin" / "python"
    
    if not python_path.exists():
        python_path = "python"
    
    # 设置PYTHONPATH环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "backend")
    
    cmd = [str(python_path), "-m", "uvicorn", "app:app", 
           "--host", "0.0.0.0", "--port", "8000", "--reload"]
    
    return subprocess.Popen(cmd, cwd=str(project_root / "backend"), env=env)

def start_frontend():
    """启动前端服务"""
    project_root = get_project_root()
    frontend_script = project_root / "web" / "start_server.py"
    
    if not frontend_script.exists():
        create_frontend_server()
    
    print("[Frontend] 启动前端服务...")
    
    # 检查虚拟环境
    if sys.platform == "win32":
        python_path = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        python_path = project_root / ".venv" / "bin" / "python"
    
    if not python_path.exists():
        python_path = "python"
    
    os.chdir(project_root / "web")
    cmd = [str(python_path), "start_server.py"]
    
    return subprocess.Popen(cmd)

def create_frontend_server():
    """创建前端服务器脚本"""
    project_root = get_project_root()
    server_script = project_root / "web" / "start_server.py"
    
    content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端静态文件服务器
"""
import http.server
import socketserver
import os
import sys
import platform
import io
from pathlib import Path

# 设置Windows控制台UTF-8编码
if platform.system().lower() == 'windows':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

def main():
    """启动前端服务器"""
    PORT = 8080
    
    # 设置静态文件目录
    web_dir = Path(__file__).parent
    os.chdir(web_dir)
    
    # 自定义处理器，支持SPA路由
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            # 如果请求的是API路径，直接返回404
            if self.path.startswith('/api/'):
                self.send_error(404)
                return
            
            # 如果文件不存在且不是根路径，返回index.html（SPA支持）
            if self.path != '/' and not os.path.exists(self.path.lstrip('/')):
                self.path = '/templates/index.html'
            elif self.path == '/':
                self.path = '/templates/index.html'
            
            return super().do_GET()
    
    print("=" * 70)
    print("  [Frontend] Professional Code Development Platform")
    print("  Frontend Static File Server")
    print("=" * 70)
    print()
    print(f"[OK] 前端服务已启动: http://localhost:{PORT}")
    print(f"[Info] 静态文件目录: {web_dir}")
    print(f"[Info] 按 Ctrl+C 停止服务")
    print("=" * 70)
    print()
    
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\n[Info] 前端服务已停止")

if __name__ == "__main__":
    main()
'''
    
    server_script.write_text(content, encoding='utf-8')

def main():
    """主函数"""
    print("=" * 60)
    print("Professional Code Development Platform")
    print("LLM 代码生成平台启动器")
    print("=" * 60)
    
    # 检查项目结构
    project_root = get_project_root()
    if not (project_root / "backend").exists():
        print("[ERROR] 未找到后端目录")
        print("[INFO] 请确保项目结构正确")
        sys.exit(1)
    
    # 启动服务
    backend_process = None
    frontend_process = None
    
    try:
        # 启动后端
        backend_process = start_backend()
        time.sleep(3)  # 等待后端启动
        
        # 启动前端
        frontend_process = start_frontend()
        time.sleep(2)  # 等待前端启动
        
        print("=" * 60)
        print("[SUCCESS] 服务启动完成！")
        print("[Frontend] 前端界面: http://localhost:8080")
        print("[Backend]  后端API: http://localhost:8000")
        print("[Docs]     API文档: http://localhost:8000/docs")
        print("=" * 60)
        print("[INFO] 按 Ctrl+C 停止所有服务")
        
        # 等待用户中断
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] 正在停止服务...")
            
    finally:
        # 清理进程
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        print("[INFO] 所有服务已停止")

if __name__ == "__main__":
    main()
