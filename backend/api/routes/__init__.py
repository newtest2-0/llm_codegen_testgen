"""
API路由模块
"""
from fastapi import APIRouter
from .generation import router as generation_router
from .evaluation import router as evaluation_router
from .system import router as system_router
from .testing import router as testing_router
from .settings import router as settings_router
from .review import router as review_router
from .knowledge import router as knowledge_router

# 创建主路由器
router = APIRouter()

# 注册子路由
router.include_router(generation_router, prefix="/generation", tags=["代码生成"])
router.include_router(evaluation_router, prefix="/evaluation", tags=["代码评估"])
router.include_router(testing_router, prefix="/testing", tags=["智能测试"])
router.include_router(system_router, prefix="/system", tags=["系统管理"])
router.include_router(settings_router, prefix="/settings", tags=["系统设置"])
router.include_router(review_router, tags=["审阅系统"])
router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库"])

__all__ = ["router"]
