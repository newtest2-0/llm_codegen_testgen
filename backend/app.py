"""
主应用程序入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import config
from core.providers import ProviderManager
from api.routes import router
from api.middleware import setup_middleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
provider_manager: ProviderManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global provider_manager
    
    # 启动时初始化
    logger.info("[Start] 启动LLM代码生成平台...")
    
    # 初始化提供者管理器
    provider_manager = ProviderManager(config._config)
    app.state.provider_manager = provider_manager
    
    logger.info(f"[OK] 已加载 {len(provider_manager)} 个AI提供者")
    logger.info(f"[Info] 可用提供者: {', '.join(provider_manager.get_provider_names())}")
    
    yield
    
    # 关闭时清理
    logger.info("[Stop] 关闭LLM代码生成平台...")

def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    
    Returns:
        FastAPI应用实例
    """
    # 检查是否启用增强评估
    enhanced_enabled = False
    try:
        from core.evaluators.enhanced import EnhancedCodeEvaluator
        enhanced_enabled = True
        logger.info("[OK] 增强版代码评测系统已加载")
    except ImportError as e:
        logger.warning(f"[WARN] 增强版代码评测系统不可用: {e}")
        logger.info("[Info] 运行 'python scripts/install_enhanced.py' 安装依赖")
    
    # 更新配置
    config.set("enhanced_evaluation.enabled", enhanced_enabled)
    
    # 创建应用
    app = FastAPI(
        title="LLM 代码生成平台",
        description="一个轻量级的大模型代码生成、测试生成和评测系统",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # 设置中间件
    setup_middleware(app)
    
    # 注册路由
    app.include_router(router, prefix="/api/v1")
    
    # 健康检查端点（保持向后兼容）
    @app.get("/health")
    async def health_check():
        """健康检查"""
        provider_manager = getattr(app.state, 'provider_manager', None)
        if provider_manager:
            return {
                "ok": True,
                "providers": provider_manager.get_provider_names(),
                "enhanced_evaluation": config.get("enhanced_evaluation.enabled", False)
            }
        return {"ok": False, "error": "Provider manager not initialized"}
    
    return app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    server_config = config.server_config
    uvicorn.run(
        "backend.app:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=server_config.get("reload", True)
    )