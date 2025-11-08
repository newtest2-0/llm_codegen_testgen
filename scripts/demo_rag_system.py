#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG知识库系统演示脚本
展示JSON文件存储和检索机制
"""
import sys
import io
import platform
from pathlib import Path

# 设置Windows控制台UTF-8编码
if platform.system().lower() == 'windows':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from core.rag import KnowledgeBase, KnowledgeRetriever, TextEmbedder


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def demo_storage():
    """演示存储机制"""
    print_section("1. JSON文件存储演示")
    
    print("\n[Info] 知识库存储位置:")
    storage_path = project_root / "data" / "knowledge_base.json"
    print(f"  路径: {storage_path}")
    print(f"  存在: {'是' if storage_path.exists() else '否（首次使用时自动创建）'}")
    
    print("\n[Step] 创建知识库实例...")
    kb = KnowledgeBase(str(storage_path))
    print(f"[OK] 已加载 {len(kb.entries)} 条知识")
    
    print("\n[Step] 添加示例知识...")
    entry_id = kb.add_entry(
        requirement="实现快速排序算法，支持升序降序",
        code="def quick_sort(arr, reverse=False):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    if reverse:\n        return quick_sort(right, True) + middle + quick_sort(left, True)\n    return quick_sort(left) + middle + quick_sort(right)",
        language="python",
        tags=["algorithm", "sorting"],
        quality_score=0.92,
        test_results={"passed": True, "coverage": 0.95}
    )
    print(f"[OK] 添加成功，条目ID: {entry_id}")
    print(f"[OK] JSON文件已自动保存到: {storage_path}")
    
    print("\n[Info] JSON文件内容预览:")
    if storage_path.exists():
        import json
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"  版本: {data['version']}")
            print(f"  更新时间: {data['updated_at']}")
            print(f"  条目数: {data['count']}")
            print(f"  第一个条目:")
            if data['entries']:
                entry = data['entries'][0]
                print(f"    - ID: {entry['id']}")
                print(f"    - 需求: {entry['requirement'][:50]}...")
                print(f"    - 语言: {entry['language']}")
                print(f"    - 质量: {entry['quality_score']}")
                print(f"    - 标签: {', '.join(entry['tags'])}")


def demo_retrieval():
    """演示检索机制"""
    print_section("2. 智能检索机制演示")
    
    storage_path = project_root / "data" / "knowledge_base.json"
    kb = KnowledgeBase(str(storage_path))
    embedder = TextEmbedder()
    retriever = KnowledgeRetriever(kb, embedder)
    
    print("\n[Step] 添加多个示例知识...")
    
    # 添加几个不同类型的知识
    examples = [
        {
            "requirement": "实现二分查找算法，在有序数组中查找目标值",
            "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
            "language": "python",
            "tags": ["algorithm", "search"],
            "quality_score": 0.95
        },
        {
            "requirement": "实现用户认证系统，支持JWT token",
            "code": "import jwt\ndef authenticate(username, password):\n    # 验证逻辑\n    token = jwt.encode({'user': username}, SECRET_KEY)\n    return token",
            "language": "python",
            "tags": ["security", "api"],
            "quality_score": 0.88
        }
    ]
    
    for ex in examples:
        kb.add_entry(**ex)
        print(f"[OK] 添加: {ex['requirement'][:40]}...")
    
    print(f"\n[OK] 当前知识库共有 {len(kb.entries)} 条记录")
    print(f"[OK] 存储位置: {storage_path}")
    
    print("\n" + "-" * 80)
    print("[Demo] 检索演示")
    print("-" * 80)
    
    # 测试查询1：查找排序相关
    print("\n[Query 1] 查询: '实现归并排序算法'")
    results = retriever.retrieve("实现归并排序算法", top_k=3, language="python")
    
    print(f"[Result] 找到 {len(results)} 条相关记录:\n")
    for i, result in enumerate(results, 1):
        entry = result.entry
        print(f"  {i}. 相似度: {result.score:.3f} | 质量: {entry.quality_score:.2f}")
        print(f"     需求: {entry.requirement[:50]}...")
        print(f"     标签: {', '.join(entry.tags)}")
        print()
    
    # 测试查询2：查找认证相关
    print("\n[Query 2] 查询: '实现用户登录功能'")
    results = retriever.retrieve("实现用户登录功能", top_k=3, language="python")
    
    print(f"[Result] 找到 {len(results)} 条相关记录:\n")
    for i, result in enumerate(results, 1):
        entry = result.entry
        print(f"  {i}. 相似度: {result.score:.3f} | 质量: {entry.quality_score:.2f}")
        print(f"     需求: {entry.requirement[:50]}...")
        print(f"     标签: {', '.join(entry.tags)}")
        print()


def demo_enhanced_prompt():
    """演示增强Prompt"""
    print_section("3. 增强Prompt生成演示")
    
    storage_path = project_root / "data" / "knowledge_base.json"
    kb = KnowledgeBase(str(storage_path))
    embedder = TextEmbedder()
    retriever = KnowledgeRetriever(kb, embedder)
    
    print("\n[Query] 需求: '实现堆排序算法'")
    
    enhanced_prompt = retriever.build_enhanced_prompt(
        requirement="实现堆排序算法",
        language="python",
        top_k=2
    )
    
    print("\n[Result] 生成的增强Prompt:")
    print("-" * 80)
    print(enhanced_prompt[:500] + "...")
    print("-" * 80)
    
    print("\n[Explain] Prompt增强效果:")
    print("  - 原始Prompt: 只有需求描述（约50字）")
    print("  - 增强Prompt: 包含需求 + 2个参考案例（约500字）")
    print("  - AI可以参考成功案例的设计思路")
    print("  - 生成的代码质量显著提升！")


def demo_file_structure():
    """演示文件结构"""
    print_section("4. JSON文件结构说明")
    
    print("\n[Structure] knowledge_base.json 文件结构:")
    print("""
{
  "version": "1.0",                    ← 知识库版本
  "updated_at": "2024-11-08T12:00:00", ← 最后更新时间
  "count": 3,                          ← 条目总数
  "entries": [                         ← 知识条目数组
    {
      "id": "abc123",                  ← 唯一ID
      "requirement": "实现快速排序...", ← 需求描述
      "code": "def quick_sort...",     ← 代码实现
      "language": "python",            ← 编程语言
      "tags": ["algorithm"],           ← 标签
      "quality_score": 0.92,           ← 质量分数
      "test_results": {...},           ← 测试结果
      "metadata": {...},               ← 元数据
      "created_at": "2024-11-08..."    ← 创建时间
    }
  ]
}
    """)
    
    print("\n[Access] 如何查看文件:")
    print("  1. 直接打开文件:")
    print("     notepad data\\knowledge_base.json")
    print()
    print("  2. 通过API查看:")
    print("     http://localhost:8000/api/v1/knowledge/list")
    print()
    print("  3. 通过前端查看:")
    print("     点击界面上的【知识库】按钮")


def demo_retrieval_process():
    """演示检索过程"""
    print_section("5. 检索工作流程")
    
    print("""
[工作流程]

1. 系统启动
   ↓
   加载 data/knowledge_base.json
   ↓
   解析JSON → 创建KnowledgeEntry对象
   ↓
   存储在内存: entries = [对象1, 对象2, ...]

2. 用户查询 "实现归并排序"
   ↓
   文本向量化: [0.2, 0.5, 0.3, ..., 0.8]  (384维向量)
   ↓
   遍历内存中的所有条目
   ↓
   for entry in entries:
       entry_vec = embed(entry.requirement)
       similarity = cosine_similarity(query_vec, entry_vec)
       score = similarity × (0.7 + 0.3 × quality_score)
   ↓
   按分数排序，返回Top 3

3. 自动保存（质量>0.8时）
   ↓
   添加新条目到内存 entries.append(new_entry)
   ↓
   序列化为JSON
   ↓
   写入 data/knowledge_base.json

[性能]
- 检索速度: 毫秒级（内存检索）
- 文件大小: 1000条记录约2-3MB
- 加载时间: <1秒
    """)


def main():
    """主函数"""
    print("=" * 80)
    print("  RAG知识库系统 - 存储与检索机制演示")
    print("  Professional Code Development Platform")
    print("=" * 80)
    
    print("\n[提示] 本演示将展示:")
    print("  1. JSON文件存储机制")
    print("  2. 智能检索机制")
    print("  3. 增强Prompt生成")
    print("  4. 文件结构说明")
    print("  5. 检索工作流程")
    
    try:
        demo_storage()
        demo_retrieval()
        demo_enhanced_prompt()
        demo_file_structure()
        demo_retrieval_process()
        
        print_section("演示完成")
        print("\n[Summary] 核心要点:")
        print("  ✅ JSON文件位置: data/knowledge_base.json")
        print("  ✅ 系统启动时: 自动加载JSON到内存")
        print("  ✅ 检索机制: 基于向量相似度计算（毫秒级）")
        print("  ✅ 保存机制: 每次修改立即写入JSON文件")
        print("  ✅ AI使用: 复用你已配置的AI模型（OpenAI/DeepSeek等）")
        print()
        print("[Next] 运行以下命令查看实际文件:")
        print("  notepad data\\knowledge_base.json")
        print()
        
    except Exception as e:
        print(f"\n[ERROR] 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    
    if platform.system().lower() == "windows":
        input("\n按回车键退出...")
    
    sys.exit(exit_code)

