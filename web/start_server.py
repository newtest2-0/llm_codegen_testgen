#!/usr/bin/env python3
"""
前端静态文件服务器
"""
import http.server
import socketserver
import os
from pathlib import Path

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
    
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"✅ 前端服务已启动: http://localhost:{PORT}")
        print("按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 前端服务已停止")

if __name__ == "__main__":
    main()
