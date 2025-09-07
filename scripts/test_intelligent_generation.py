#!/usr/bin/env python3
"""
智能测试生成功能演示脚本
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_intelligent_test_generation():
    """测试智能测试生成功能"""
    print("=" * 60)
    print("🧪 智能测试生成功能演示")
    print("=" * 60)
    
    # 演示代码
    demo_code = '''def solve(numbers):
    """
    计算数字列表的平均值
    """
    if not numbers:
        return 0
    
    total = sum(numbers)
    return total / len(numbers)
'''
    
    requirement = "实现一个计算数字列表平均值的函数，需要处理空列表的情况"
    
    print("📝 演示代码：")
    print(demo_code)
    print(f"📋 需求描述：{requirement}")
    print()
    
    # 1. 测试代码分析
    print("🔍 步骤1：分析代码结构...")
    try:
        analysis_response = requests.post(
            f"{API_BASE}/api/v1/testing/analyze-code",
            json={"code": demo_code},
            timeout=30
        )
        
        if analysis_response.status_code == 200:
            analysis = analysis_response.json()["analysis"]
            print("✅ 代码分析成功！")
            print(f"   - 主函数：{analysis.get('main_function', {}).get('name', 'N/A')}")
            print(f"   - 参数数量：{len(analysis.get('parameters', []))}")
            print(f"   - 复杂度：{analysis.get('complexity', 'N/A')}")
            print(f"   - 包含循环：{analysis.get('main_function', {}).get('has_loops', False)}")
            print(f"   - 包含条件：{analysis.get('main_function', {}).get('has_conditions', False)}")
        else:
            print(f"❌ 代码分析失败：{analysis_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 分析请求失败：{e}")
        return False
    
    print()
    
    # 2. 测试智能测试生成
    print("🤖 步骤2：生成智能测试用例...")
    try:
        test_response = requests.post(
            f"{API_BASE}/api/v1/testing/generate-test",
            json={
                "code": demo_code,
                "requirement": requirement,
                "test_strategy": "intelligent"
            },
            timeout=60
        )
        
        if test_response.status_code == 200:
            test_result = test_response.json()
            print("✅ 智能测试生成成功！")
            print(f"   - 使用策略：{test_result['strategy_used']}")
            print("\n📄 生成的测试代码：")
            print("-" * 50)
            print(test_result["tests_code"])
            print("-" * 50)
        else:
            print(f"❌ 测试生成失败：{test_response.status_code}")
            print(f"错误详情：{test_response.text}")
            return False
    except Exception as e:
        print(f"❌ 测试生成请求失败：{e}")
        return False
    
    print()
    
    # 3. 测试完整的代码生成+智能测试流程
    print("🚀 步骤3：完整流程演示（代码生成 + 智能测试）...")
    try:
        generation_response = requests.post(
            f"{API_BASE}/api/v1/generation/generate",
            json={
                "requirement": "实现一个函数，计算给定字符串中每个字符的出现次数",
                "language": "python",
                "providers": ["openai", "deepseek"],  # 使用多个提供者
                "extra_directives": "返回字典格式，键为字符，值为出现次数"
            },
            timeout=90
        )
        
        if generation_response.status_code == 200:
            result = generation_response.json()
            print("✅ 代码生成和智能测试完成！")
            print(f"   - 会话ID：{result['session_id']}")
            print(f"   - 生成方案数：{len(result['artifacts'])}")
            
            # 显示生成的代码
            for i, artifact in enumerate(result['artifacts']):
                print(f"\n📝 方案 {i+1} ({artifact['provider']}):")
                print(artifact['code'][:200] + "..." if len(artifact['code']) > 200 else artifact['code'])
            
            # 显示智能生成的测试
            if result.get('tests_code'):
                print("\n🧪 智能生成的测试用例：")
                test_lines = result['tests_code'].split('\n')
                for line in test_lines[:20]:  # 显示前20行
                    print(line)
                if len(test_lines) > 20:
                    print("...")
            
        else:
            print(f"❌ 完整流程失败：{generation_response.status_code}")
            print(f"错误详情：{generation_response.text}")
            return False
    except Exception as e:
        print(f"❌ 完整流程请求失败：{e}")
        return False
    
    print()
    print("🎉 智能测试生成功能演示完成！")
    return True

def test_api_endpoints():
    """测试新的API端点"""
    print("\n" + "=" * 60)
    print("🔧 API端点测试")
    print("=" * 60)
    
    endpoints = [
        "/api/v1/testing/test-strategies",
        "/api/v1/testing/demo-generate"
    ]
    
    for endpoint in endpoints:
        print(f"📡 测试端点：{endpoint}")
        try:
            if endpoint.endswith("demo-generate"):
                response = requests.post(f"{API_BASE}{endpoint}", timeout=60)
            else:
                response = requests.get(f"{API_BASE}{endpoint}", timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ 状态码：{response.status_code}")
                data = response.json()
                if "strategies" in data:
                    print(f"   📋 可用策略数：{len(data['strategies'])}")
                elif "message" in data:
                    print(f"   📄 响应：{data['message'][:100]}...")
            else:
                print(f"   ❌ 状态码：{response.status_code}")
        except Exception as e:
            print(f"   ❌ 请求失败：{e}")
    
    print("\n🔚 API端点测试完成")

def main():
    """主函数"""
    print("🎯 LLM代码生成平台 - 智能测试功能演示")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ 后端服务未运行，请先启动服务")
            print("提示：运行 python scripts/start.py")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到后端服务，请先启动服务")
        print("提示：运行 python scripts/start.py")
        return
    
    print("✅ 服务连接正常")
    print()
    
    # 运行演示
    success = test_intelligent_test_generation()
    
    if success:
        test_api_endpoints()
        print("\n🎊 所有演示完成！")
        print("\n💡 您现在可以：")
        print("   1. 访问 http://localhost:8080 使用Web界面")
        print("   2. 访问 http://localhost:8000/docs 查看API文档")
        print("   3. 体验智能测试生成功能的强大能力")
    else:
        print("\n😞 演示过程中出现错误")

if __name__ == "__main__":
    main()
