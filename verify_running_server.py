"""测试运行中的服务器路由"""
import requests
import json

try:
    # 测试服务器是否在运行
    print("[TEST] Checking if server is running...")
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"[OK] Server is running: {response.status_code}")

    # 获取OpenAPI规范以查看所有路由
    print("\n[TEST] Fetching OpenAPI spec...")
    response = requests.get("http://localhost:8000/openapi.json", timeout=5)

    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get('paths', {})

        # 查找requirements相关路由
        req_paths = [p for p in paths.keys() if 'requirements' in p]

        print(f"[INFO] Total API paths: {len(paths)}")
        print(f"[INFO] Requirements paths: {len(req_paths)}")

        if req_paths:
            print("\n[OK] Requirements routes found:")
            for path in sorted(req_paths):
                methods = list(paths[path].keys())
                print(f"     - {', '.join([m.upper() for m in methods])} {path}")
        else:
            print("\n[ERROR] No requirements routes found!")
            print("[INFO] Available paths:")
            for path in sorted(paths.keys())[:20]:
                print(f"     - {path}")
    else:
        print(f"[ERROR] Failed to get OpenAPI spec: {response.status_code}")

    # 测试创建文档的端点
    print("\n[TEST] Testing document creation endpoint...")
    response = requests.post(
        "http://localhost:8000/api/v1/requirements/documents",
        json={"project_name": "Test Project", "sections": {}},
        timeout=5
    )
    print(f"[RESULT] POST /api/v1/requirements/documents -> {response.status_code}")
    if response.status_code == 200:
        doc = response.json()
        print(f"[OK] Document created: {doc.get('doc_id')}")

        # 测试LLM评阅端点
        doc_id = doc.get('doc_id')
        print(f"\n[TEST] Testing LLM review endpoint...")
        response = requests.post(
            f"http://localhost:8000/api/v1/requirements/documents/{doc_id}/llm-review",
            json={"section_type": "detailed_requirement", "content": "Test content"},
            timeout=30
        )
        print(f"[RESULT] POST /api/v1/requirements/documents/{doc_id}/llm-review -> {response.status_code}")
        if response.status_code == 200:
            print("[OK] LLM review endpoint is working!")
        else:
            print(f"[ERROR] LLM review failed: {response.text}")
    else:
        print(f"[ERROR] Document creation failed: {response.text}")

except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to server. Is it running on port 8000?")
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
