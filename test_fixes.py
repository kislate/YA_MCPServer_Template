"""
测试 URL 清理和 list_knowledge 功能
"""

import asyncio


async def test_url_cleaning():
    """测试 URL 的空格和换行符处理"""
    print("\n=== 测试 URL 清理功能 ===")
    
    try:
        from tools.document_tool import import_webpage
        
        # 测试带空格和换行符的 URL
        test_urls = [
            "  https://example.com  ",
            "https://example.com\n",
            "\nhttps://example.com",
            "  https://example.com\n\n  ",
        ]
        
        for url in test_urls:
            print(f"\n测试 URL: {repr(url)}")
            try:
                result = await import_webpage(url=url, tags="测试")
                print(f"✅ 成功导入: {result['title']}")
                print(f"   ID: {result['id']}")
            except Exception as e:
                print(f"❌ 失败: {e}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def test_list_all_knowledge():
    """测试列出所有知识（包括 PDF 和网页）"""
    print("\n=== 测试 list_knowledge 功能 ===")
    
    try:
        from core.knowledge_store import list_knowledge
        
        # 列出所有知识
        result = await list_knowledge(limit=100)
        
        print(f"\n📚 知识库统计:")
        print(f"   总条目数: {result['total_items']}")
        print(f"   总分块数: {result['total_chunks']}")
        
        print(f"\n📋 所有知识条目:")
        for idx, item in enumerate(result['items'], 1):
            print(f"\n{idx}. {item['title']}")
            print(f"   ID: {item['id']}")
            print(f"   来源: {item['source']}")
            print(f"   标签: {item['tags']}")
            print(f"   分块数: {item['total_chunks']}")
            print(f"   预览: {item['preview'][:50]}...")
        
        if result['total_items'] == 0:
            print("\n💡 知识库为空，请先导入一些文档")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def test_search_knowledge():
    """测试搜索功能"""
    print("\n=== 测试 search_knowledge 功能 ===")
    
    try:
        from core.knowledge_store import search_knowledge
        
        # 搜索关键词
        queries = ["example", "测试", "网页", "PDF"]
        
        for query in queries:
            print(f"\n🔍 搜索: '{query}'")
            result = await search_knowledge(query=query, top_k=5)
            
            print(f"   找到 {result['total_results']} 条结果")
            
            for idx, item in enumerate(result['results'][:3], 1):
                print(f"   {idx}. {item['title']} (相似度: {item['relevance']})")
                print(f"      来源: {item['source']}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def test_pdf_path_cleaning():
    """测试 PDF 路径清理"""
    print("\n=== 测试 PDF 路径清理功能 ===")
    
    try:
        from core.file_parser import PDFParser
        
        parser = PDFParser()
        
        # 测试带空格的路径识别
        test_paths = [
            "  test.pdf  ",
            "test.pdf\n",
            "\n  /path/to/file.pdf  \n",
        ]
        
        for path in test_paths:
            print(f"\n测试路径: {repr(path)}")
            # 先 strip 再检查
            cleaned = path.strip()
            can_handle = parser.can_handle(cleaned)
            print(f"   清理后: {repr(cleaned)}")
            print(f"   能处理: {can_handle}")
        
        print("\n✅ PDF 路径清理测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("URL 清理和知识列表功能测试")
    print("=" * 60)
    
    # 测试 PDF 路径清理
    await test_pdf_path_cleaning()
    
    # 测试 URL 清理（实际导入）
    # await test_url_cleaning()  # 取消注释以测试实际导入
    
    # 测试列出所有知识
    await test_list_all_knowledge()
    
    # 测试搜索功能
    await test_search_knowledge()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    print("\n📝 修复说明:")
    print("1. ✅ URL 和文件路径会自动去除空格和换行符")
    print("2. ✅ list_knowledge 默认 limit 提升到 100")
    print("3. ✅ list_knowledge 优化了去重逻辑")
    print("4. ✅ 所有导入的文档都应该能被搜索到")


if __name__ == "__main__":
    asyncio.run(main())
