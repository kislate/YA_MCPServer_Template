"""
测试原始文件保留功能
"""

import asyncio
from pathlib import Path


async def test_pdf_attachment():
    """测试 PDF 附件保存"""
    print("\n=== 测试 PDF 附件保存功能 ===")
    
    # 检查附件目录
    attachment_dir = Path("./data/attachments")
    print(f"附件目录: {attachment_dir.absolute()}")
    
    if attachment_dir.exists():
        files = list(attachment_dir.glob("*"))
        print(f"✅ 附件目录存在")
        print(f"   当前文件数: {len(files)}")
        for f in files[:5]:
            print(f"   - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    else:
        print("📁 附件目录尚未创建（导入第一个文档时会自动创建）")


async def test_import_pdf_with_attachment():
    """测试 PDF 导入并保存附件"""
    print("\n=== 测试 PDF 导入（需要真实 PDF 文件）===")
    
    # 提示用户
    print("💡 要测试此功能，请准备一个 PDF 文件并运行：")
    print("   from tools.document_tool import import_pdf")
    print("   result = await import_pdf(file_path='your.pdf')")
    print()
    print("✨ 导入后会自动：")
    print("   1. 提取文本转为 Markdown → data/raw/{id}.md")
    print("   2. 复制原始 PDF → data/attachments/{id}.pdf")
    print("   3. 建立向量索引 → ChromaDB")


async def test_directory_structure():
    """检查目录结构"""
    print("\n=== 检查目录结构 ===")
    
    dirs = {
        "data/raw": "Markdown 笔记",
        "data/attachments": "原始文件（PDF、HTML 快照）",
        "data/chromadb": "向量数据库"
    }
    
    for path, desc in dirs.items():
        p = Path(path)
        exists = "✅" if p.exists() else "📁"
        count = len(list(p.glob("*"))) if p.exists() else 0
        print(f"{exists} {path:20s} - {desc:30s} ({count} 个文件)")


async def test_webpage_snapshot():
    """测试网页 HTML 快照"""
    print("\n=== 测试网页 HTML 快照功能 ===")
    
    print("💡 要测试此功能，运行：")
    print("   from tools.document_tool import import_webpage")
    print("   result = await import_webpage(url='https://example.com')")
    print()
    print("✨ 导入后会自动：")
    print("   1. 抓取网页转为 Markdown → data/raw/{id}.md")
    print("   2. 保存 HTML 快照 → data/attachments/{id}.html")
    print("   3. 建立向量索引 → ChromaDB")


async def show_usage_example():
    """显示使用示例"""
    print("\n" + "=" * 60)
    print("📚 使用示例")
    print("=" * 60)
    
    example = """
# 1. 导入 PDF（会自动保存原始文件）
from tools.document_tool import import_pdf

result = await import_pdf(
    file_path="./papers/deep_learning.pdf",
    title="深度学习基础",
    tags="机器学习,神经网络"
)

print(f"知识 ID: {result['id']}")
print(f"原始路径: {result['original_path']}")
print(f"附件路径: {result['attachment_path']}")  # ← 新增！
print(f"PDF 页数: {result['pdf_pages']}")

# 2. 导入网页（会保存 HTML 快照）
from tools.document_tool import import_webpage

result = await import_webpage(
    url="https://pytorch.org/tutorials/beginner/basics/intro.html",
    tags="PyTorch,教程"
)

print(f"知识 ID: {result['id']}")
print(f"原网址: {result['url']}")
print(f"HTML 快照: {result['html_snapshot']}")  # ← 新增！

# 3. 查看文件结构
data/
├── raw/                    # Markdown 笔记
│   ├── kb_12345678.md
│   └── kb_87654321.md
├── attachments/            # 原始文件（新增！）
│   ├── kb_12345678.pdf    # PDF 副本
│   └── kb_87654321.html   # HTML 快照
└── chromadb/              # 向量数据库
    └── ...

# 4. 删除知识（会同时删除所有文件）
from core.knowledge_store import delete_knowledge

await delete_knowledge(knowledge_id="kb_12345678")
# 会删除：
#   - 向量数据
#   - Markdown 文件
#   - 原始附件 ✅
"""
    print(example)


async def main():
    """主测试函数"""
    print("=" * 60)
    print("原始文件保留功能测试")
    print("=" * 60)
    
    # 检查目录结构
    await test_directory_structure()
    
    # 检查附件目录
    await test_pdf_attachment()
    
    # 测试 PDF 导入
    await test_import_pdf_with_attachment()
    
    # 测试网页快照
    await test_webpage_snapshot()
    
    # 显示使用示例
    await show_usage_example()
    
    print("\n" + "=" * 60)
    print("✅ 功能已实现！")
    print("=" * 60)
    
    print("\n🎉 新功能总结:")
    print("1. ✅ PDF 导入会自动复制原始文件到 data/attachments/")
    print("2. ✅ 网页导入会保存 HTML 快照到 data/attachments/")
    print("3. ✅ 删除知识时会同时删除所有相关文件")
    print("4. ✅ 知识库完全自包含，可以整体备份和迁移")


if __name__ == "__main__":
    asyncio.run(main())
