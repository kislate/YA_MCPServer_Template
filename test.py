"""端到端测试脚本 - 测试完可删除"""
import asyncio

async def test():
    from core.knowledge_store import add_knowledge, search_knowledge, get_stats, delete_knowledge

    # 1. 添加知识
    print("=== 添加知识 ===")
    result = await add_knowledge(
        content="Python 装饰器是一种设计模式，允许在不修改函数代码的情况下扩展函数行为。"
                "使用 @decorator 语法糖可以简洁地应用装饰器。"
                "常见的内置装饰器有 @staticmethod, @classmethod, @property 等。",
        title="Python装饰器笔记",
        tags="python,编程",
        source="课堂笔记",
    )
    print(f"添加成功: id={result['id']}, chunks={result['chunks_count']}")
    kid = result["id"]

    # 2. 语义搜索
    print("\n=== 语义搜索 ===")
    search = await search_knowledge(query="什么是装饰器", top_k=3)
    print(f"搜索到 {search['total_results']} 条结果:")
    for r in search["results"]:
        print(f"  相关度={r['relevance']:.4f}  内容={r['content'][:50]}...")

    # 3. 统计
    print("\n=== 知识库统计 ===")
    stats = await get_stats()
    print(f"知识条目: {stats['total_items']}, 总分块: {stats['total_chunks']}")
    print(f"标签: {stats['tags']}")

    # 4. 删除
    print("\n=== 删除测试数据 ===")
    d = await delete_knowledge(kid)
    print(d["message"])

    print("\n✅ 所有测试通过！")

asyncio.run(test())
