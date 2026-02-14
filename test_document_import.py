"""
文档导入功能测试脚本

测试 PDF 和网页导入功能是否正常工作
"""

import asyncio
from pathlib import Path


async def test_pdf_parser():
    """测试 PDF 解析器"""
    print("\n=== 测试 PDF 解析器 ===")
    
    try:
        from core.file_parser import PDFParser
        
        parser = PDFParser()
        
        # 检查能否识别 PDF
        assert parser.can_handle("test.pdf") == True
        assert parser.can_handle("https://example.com") == False
        
        print("✅ PDF 解析器初始化成功")
        print("✅ 文件类型识别正常")
        
        # 实际解析需要真实 PDF 文件
        print("\n💡 提示：要测试实际解析，请提供一个 PDF 文件路径")
        
    except Exception as e:
        print(f"❌ PDF 解析器测试失败: {e}")


async def test_webpage_parser():
    """测试网页解析器"""
    print("\n=== 测试网页解析器 ===")
    
    try:
        from core.file_parser import WebPageParser
        
        parser = WebPageParser()
        
        # 检查能否识别 URL
        assert parser.can_handle("https://example.com") == True
        assert parser.can_handle("http://test.org") == True
        assert parser.can_handle("test.pdf") == False
        
        print("✅ 网页解析器初始化成功")
        print("✅ URL 类型识别正常")
        
        # 测试简单网页（小型测试网站）
        print("\n📡 测试抓取示例网页...")
        result = await parser.parse("https://example.com")
        
        print(f"✅ 网页抓取成功")
        print(f"   标题: {result['title']}")
        print(f"   内容长度: {len(result['content'])} 字符")
        print(f"   URL: {result['metadata']['url']}")
        
    except Exception as e:
        print(f"❌ 网页解析器测试失败: {e}")


async def test_document_factory():
    """测试文档解析器工厂"""
    print("\n=== 测试文档解析器工厂 ===")
    
    try:
        from core.file_parser import DocumentParserFactory
        
        factory = DocumentParserFactory()
        
        print("✅ 工厂初始化成功")
        print(f"   已注册 {len(factory.parsers)} 个解析器")
        
        # 测试自动选择
        print("\n📡 测试自动选择解析器...")
        result = await factory.parse("https://example.com")
        
        print(f"✅ 自动识别并解析成功")
        print(f"   文档类型: {result['metadata']['doc_type']}")
        print(f"   标题: {result['title']}")
        
    except Exception as e:
        print(f"❌ 文档工厂测试失败: {e}")


async def test_import_tools():
    """测试导入工具是否能正常加载"""
    print("\n=== 测试导入工具 ===")
    
    try:
        from tools.document_tool import import_pdf, import_webpage, import_document
        
        print("✅ import_pdf 工具加载成功")
        print("✅ import_webpage 工具加载成功")
        print("✅ import_document 工具加载成功")
        
        # 检查工具元数据
        print(f"\n📋 import_pdf 描述: {import_pdf.__doc__.strip().split('Args:')[0].strip()}")
        
    except Exception as e:
        print(f"❌ 工具加载失败: {e}")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("文档导入功能测试")
    print("=" * 60)
    
    # 运行所有测试
    await test_pdf_parser()
    await test_webpage_parser()
    await test_document_factory()
    await test_import_tools()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    print("\n📚 下一步：")
    print("1. 使用 import_pdf(file_path='your.pdf') 导入 PDF")
    print("2. 使用 import_webpage(url='https://...') 导入网页")
    print("3. 使用 import_document(source='...') 智能导入")
    print("\n详细文档：docs/document-import-guide.md")


if __name__ == "__main__":
    asyncio.run(main())
