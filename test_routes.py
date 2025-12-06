"""测试requirements路由导入"""
import sys
sys.path.insert(0, 'backend')

try:
    print("[TEST] Testing requirements routes import...")

    # 测试导入requirements模块
    from api.routes import requirements
    print("[OK] requirements module imported successfully")
    print(f"     Router: {requirements.router}")

    # 检查路由数量
    routes = requirements.router.routes
    print(f"     Number of routes: {len(routes)}")

    # 列出所有路由
    for route in routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"     - {list(route.methods)[0]} {route.path}")

    # 测试导入主router
    print("\n[TEST] Testing main router import...")
    from api.routes import router
    print("[OK] Main router imported successfully")

    # 检查主router的路由
    all_routes = router.routes
    print(f"     Total routes: {len(all_routes)}")

    # 查找requirements相关路由
    req_routes = [r for r in all_routes if hasattr(r, 'path') and 'requirements' in r.path]
    print(f"     Requirements routes: {len(req_routes)}")
    for route in req_routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"     - {list(route.methods)[0]} {route.path}")

    print("\n[SUCCESS] All tests passed!")

except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
