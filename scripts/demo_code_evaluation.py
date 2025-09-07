#!/usr/bin/env python3
"""
综合代码评估功能演示脚本
"""
import requests
import json

API_BASE = "http://localhost:8000"

def demo_code_evaluation():
    """演示综合代码评估功能"""
    print("=" * 70)
    print("🔍 综合代码评估系统演示")
    print("=" * 70)
    
    # 演示不同质量的代码
    test_cases = [
        {
            "name": "优秀代码示例",
            "code": '''def solve(numbers: list) -> float:
    """
    计算数字列表的平均值
    
    Args:
        numbers: 数字列表
        
    Returns:
        平均值，如果列表为空则返回0
        
    Raises:
        TypeError: 如果输入不是列表
    """
    if not isinstance(numbers, list):
        raise TypeError("输入必须是列表")
    
    if not numbers:
        return 0.0
    
    # 验证所有元素都是数字
    for num in numbers:
        if not isinstance(num, (int, float)):
            raise TypeError("列表中所有元素必须是数字")
    
    total = sum(numbers)
    return total / len(numbers)
''',
            "requirement": "实现一个安全的平均值计算函数"
        },
        {
            "name": "一般代码示例", 
            "code": '''def solve(nums):
    if len(nums)==0:
        return 0
    sum=0
    for i in range(len(nums)):
        sum=sum+nums[i]
    avg=sum/len(nums)
    return avg
''',
            "requirement": "计算数字列表平均值"
        },
        {
            "name": "问题代码示例",
            "code": '''def solve(x):
    password = "admin123"  # 硬编码密码
    import os
    if x:
        if len(x) > 0:
            if sum(x) != 0:
                if max(x) > min(x):
                    result = eval("sum(x)/len(x)")  # 危险的eval
                    os.system("echo " + str(result))  # 命令注入风险
                    return result
    return None
''',
            "requirement": "计算平均值（存在安全问题的代码）"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试案例 {i}：{test_case['name']}")
        print("-" * 50)
        
        # 显示代码
        print("代码：")
        print(test_case['code'])
        
        # 调用评估API
        try:
            response = requests.post(
                f"{API_BASE}/api/v1/evaluation/quick-evaluate",
                json={
                    "code": test_case['code'],
                    "requirement": test_case['requirement']
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\n📊 评估结果：")
                print(f"   综合得分：{result['overall_score']:.3f}")
                
                metrics = result['metrics']
                print(f"   可维护性指数：{metrics['maintainability_index']:.3f}")
                print(f"   代码风格得分：{metrics['style_score']:.3f}")
                print(f"   安全性得分：{metrics['security_score']:.3f}")
                
                complexity = metrics['complexity']
                print(f"   圈复杂度：{complexity['cyclomatic_complexity']}")
                print(f"   认知复杂度：{complexity['cognitive_complexity']}")
                print(f"   嵌套深度：{complexity['nesting_depth']}")
                
                documentation = metrics['documentation']
                print(f"   文档覆盖率：{documentation['docstring_coverage']:.1%}")
                print(f"   注释比例：{documentation['comment_ratio']:.1%}")
                
                issues = metrics['issues']
                print(f"   安全问题：{issues['security_issues_count']} 个")
                print(f"   风格违规：{issues['style_violations_count']} 个")
                print(f"   代码异味：{issues['code_smells_count']} 个")
                
                # 显示改进建议
                if result['recommendations']:
                    print(f"\n💡 改进建议：")
                    for rec in result['recommendations']:
                        print(f"   {rec}")
                
                # 显示质量等级
                score = result['overall_score']
                if score >= 0.9:
                    print(f"\n🟢 质量等级：优秀")
                elif score >= 0.7:
                    print(f"\n🟡 质量等级：良好")
                elif score >= 0.5:
                    print(f"\n🟠 质量等级：一般")
                else:
                    print(f"\n🔴 质量等级：较差")
                
            else:
                print(f"❌ 评估失败：{response.status_code}")
                print(f"错误：{response.text}")
                
        except Exception as e:
            print(f"❌ 请求失败：{e}")
        
        print("\n" + "=" * 70)

def demo_quality_standards():
    """演示质量标准API"""
    print("\n📋 代码质量标准")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_BASE}/api/v1/evaluation/quality-standards")
        
        if response.status_code == 200:
            data = response.json()
            
            print("📊 质量等级标准：")
            for level, info in data['standards'].items():
                print(f"\n🏷️  {level.upper()}：{info['description']}")
                print(f"   评分范围：{info['score_range']}")
                print(f"   标准：")
                for criteria in info['criteria']:
                    print(f"     • {criteria}")
            
            print(f"\n⚖️  评估权重配置：")
            for criterion, info in data['evaluation_criteria'].items():
                print(f"   {criterion}：{info['weight']:.0%} - {info['description']}")
                
        else:
            print(f"❌ 获取标准失败：{response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求失败：{e}")

def demo_complete_workflow():
    """演示完整的代码生成+评估工作流"""
    print("\n🚀 完整工作流演示：代码生成 → 智能测试 → 综合评估")
    print("=" * 70)
    
    requirement = "实现一个函数，判断给定的字符串是否为回文串（忽略大小写和空格）"
    
    print(f"📝 需求：{requirement}")
    
    try:
        # 1. 代码生成
        print("\n🤖 步骤1：生成代码...")
        gen_response = requests.post(
            f"{API_BASE}/api/v1/generation/generate",
            json={
                "requirement": requirement,
                "language": "python",
                "providers": ["openai", "deepseek"],
                "extra_directives": "使用清晰的变量名和适当的注释"
            },
            timeout=60
        )
        
        if gen_response.status_code == 200:
            gen_result = gen_response.json()
            print(f"✅ 代码生成完成，生成了 {len(gen_result['artifacts'])} 个方案")
            
            # 显示第一个方案
            if gen_result['artifacts']:
                first_artifact = gen_result['artifacts'][0]
                print(f"\n📄 {first_artifact['provider']} 生成的代码：")
                print(first_artifact['code'][:300] + "..." if len(first_artifact['code']) > 300 else first_artifact['code'])
                
                # 2. 评估生成的代码
                print(f"\n🔍 步骤2：评估代码质量...")
                eval_response = requests.post(
                    f"{API_BASE}/api/v1/evaluation/quick-evaluate",
                    json={
                        "code": first_artifact['code'],
                        "requirement": requirement
                    },
                    timeout=30
                )
                
                if eval_response.status_code == 200:
                    eval_result = eval_response.json()
                    print(f"✅ 评估完成，综合得分：{eval_result['overall_score']:.3f}")
                    
                    # 显示关键指标
                    metrics = eval_result['metrics']
                    print(f"   🔧 可维护性：{metrics['maintainability_index']:.3f}")
                    print(f"   🎨 代码风格：{metrics['style_score']:.3f}")
                    print(f"   🔒 安全性：{metrics['security_score']:.3f}")
                    
                    if eval_result['recommendations']:
                        print(f"\n💡 主要建议：")
                        for rec in eval_result['recommendations'][:3]:  # 显示前3个建议
                            print(f"   {rec}")
                
                else:
                    print(f"❌ 评估失败：{eval_response.status_code}")
        
        else:
            print(f"❌ 代码生成失败：{gen_response.status_code}")
            print(f"错误：{gen_response.text}")
            
    except Exception as e:
        print(f"❌ 工作流执行失败：{e}")

def main():
    """主函数"""
    print("🎯 LLM代码生成平台 - 综合代码评估功能演示")
    
    # 检查服务
    try:
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ 后端服务未运行，请先启动服务")
            return
    except:
        print("❌ 无法连接到后端服务，请先启动服务")
        return
    
    print("✅ 服务连接正常\n")
    
    # 运行演示
    demo_code_evaluation()
    demo_quality_standards()
    demo_complete_workflow()
    
    print("\n🎊 综合代码评估功能演示完成！")
    print("\n💡 新功能亮点：")
    print("   ✨ 多维度代码质量评估（功能性、可维护性、风格、安全性等）")
    print("   ✨ 智能改进建议生成")
    print("   ✨ 安全漏洞检测（硬编码密钥、命令注入、SQL注入等）")
    print("   ✨ 代码复杂度分析（圈复杂度、认知复杂度、嵌套深度）")
    print("   ✨ 代码风格检查（PEP8规范）")
    print("   ✨ 文档质量评估（注释覆盖率、文档字符串）")
    print("   ✨ 代码异味检测（长函数、重复代码等）")

if __name__ == "__main__":
    main()
