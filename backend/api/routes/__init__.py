"""
API路由模块
"""
from fastapi import APIRouter
from .generation import router as generation_router
from .evaluation import router as evaluation_router
from .system import router as system_router
from .testing import router as testing_router

# 创建主路由器
router = APIRouter()

# 注册子路由
router.include_router(generation_router, prefix="/generation", tags=["代码生成"])
router.include_router(evaluation_router, prefix="/evaluation", tags=["代码评估"])
router.include_router(testing_router, prefix="/testing", tags=["智能测试"])
router.include_router(system_router, prefix="/system", tags=["系统管理"])

__all__ = ["router"]
