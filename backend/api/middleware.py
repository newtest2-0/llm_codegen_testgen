"""
API中间件配置
"""
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI) -> None:
    """
    设置应用中间件
    
    Args:
        app: FastAPI应用实例
    """
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """记录请求日志"""
        start_time = time.time()
        
        # 记录请求开始
        logger.info(f"[Request] {request.method} {request.url}")
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录响应
        logger.info(
            f"[Response] {request.method} {request.url} - "
            f"状态码: {response.status_code} - "
            f"耗时: {process_time:.3f}s"
        )
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # 错误处理中间件
    @app.middleware("http")
    async def error_handler(request: Request, call_next):
        """全局错误处理"""
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"[ERROR] 请求处理错误: {request.method} {request.url} - {str(e)}")
            # 这里可以返回自定义错误响应
            raise
