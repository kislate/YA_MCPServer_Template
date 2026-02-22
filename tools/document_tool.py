"""
文档导入工具，包括：
- import_pdf: 导入 PDF 文档
- import_pptx: 导入 PPTX 演示文稿
- import_docx: 导入 DOCX Word 文档
- import_webpage: 导入网页笔记
- import_document: 通用文档导入（自动识别类型）
"""

from typing import Any, Dict
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="import_pdf",
    title="Import PDF Document",
    description="导入 PDF 文档到知识库。自动提取文本内容，按页面分块建立向量索引。支持学术论文、课件、电子书等",
)
async def import_pdf(
    file_path: str,
    title: str = "",
    tags: str = "",
) -> Dict[str, Any]:
    """
    导入 PDF 文档到知识库
    
    Args:
        file_path (str): PDF 文件路径（绝对路径或相对路径）
        title (str): 文档标题（留空则从文件名提取）
        tags (str): 标签（逗号分隔，留空则 AI 自动生成）
        
    Returns:
        Dict[str, Any]: 导入结果，包含知识 ID、页数、分块数等
    """
    try:
        from core.file_parser import PDFParser
        from core.knowledge_store import add_knowledge
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    
    # 清理文件路径（去除空格、换行符和引号）
    file_path = file_path.strip().strip('"').strip("'")
    
    # 解析 PDF
    parser = PDFParser()
    if not parser.can_handle(file_path):
        raise ValueError(f"文件类型错误: {file_path} 不是 PDF 文件")
    
    parsed = await parser.parse(file_path)
    
    # 构建来源信息
    source = f"PDF 文档：{parsed['metadata']['file_path']}"
    
    # 使用解析出的标题或用户指定的标题
    final_title = title if title else parsed['title']
    
    # 添加到知识库
    result = await add_knowledge(
        content=parsed['content'],
        title=final_title,
        tags=tags,
        source=source
    )
    
    # 保存原始 PDF 文件副本
    from core.knowledge_store import _save_attachment
    attachment_path = _save_attachment(
        base_id=result['id'],
        source_path=parsed['metadata']['file_path'],
        doc_type='pdf'
    )
    
    # 添加 PDF 特有的元数据
    result['pdf_pages'] = parsed['metadata']['pages']
    result['original_path'] = parsed['metadata']['file_path']
    result['attachment_path'] = attachment_path if attachment_path else "未保存"
    
    return result


@YA_MCPServer_Tool(
    name="import_pptx",
    title="Import PPTX Presentation",
    description="导入 PPTX 演示文稿到知识库。自动提取幻灯片文本和表格内容，转换为 Markdown 格式建立向量索引。支持课件、报告、培训材料等",
)
async def import_pptx(
    file_path: str,
    title: str = "",
    tags: str = "",
) -> Dict[str, Any]:
    """
    导入 PPTX 演示文稿到知识库

    Args:
        file_path (str): PPTX 文件路径（绝对路径或相对路径）
        title (str): 文档标题（留空则从文件名提取）
        tags (str): 标签（逗号分隔，留空则 AI 自动生成）

    Returns:
        Dict[str, Any]: 导入结果，包含知识 ID、幻灯片数、分块数等
    """
    try:
        from core.file_parser import PPTXParser
        from core.knowledge_store import add_knowledge
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")

    # 清理文件路径（去除空格、换行符和引号）
    file_path = file_path.strip().strip('"').strip("'")

    # 解析 PPTX
    parser = PPTXParser()
    if not parser.can_handle(file_path):
        raise ValueError(f"文件类型错误: {file_path} 不是 PPTX 文件")

    parsed = await parser.parse(file_path)

    # 构建来源信息
    source = f"PPTX 演示文稿：{parsed['metadata']['file_path']}"

    # 使用解析出的标题或用户指定的标题
    final_title = title if title else parsed['title']

    # 添加到知识库
    result = await add_knowledge(
        content=parsed['content'],
        title=final_title,
        tags=tags,
        source=source
    )

    # 保存原始 PPTX 文件副本
    from core.knowledge_store import _save_attachment
    attachment_path = _save_attachment(
        base_id=result['id'],
        source_path=parsed['metadata']['file_path'],
        doc_type='pptx'
    )

    # 添加 PPTX 特有的元数据
    result['pptx_slides'] = parsed['metadata']['slides']
    result['original_path'] = parsed['metadata']['file_path']
    result['attachment_path'] = attachment_path if attachment_path else "未保存"

    return result


@YA_MCPServer_Tool(
    name="import_docx",
    title="Import DOCX Document",
    description="导入 DOCX Word 文档到知识库。自动提取段落、标题和表格内容，保留文档结构转换为 Markdown 格式。支持报告、论文、手册等",
)
async def import_docx(
    file_path: str,
    title: str = "",
    tags: str = "",
) -> Dict[str, Any]:
    """
    导入 DOCX Word 文档到知识库

    Args:
        file_path (str): DOCX 文件路径（绝对路径或相对路径）
        title (str): 文档标题（留空则从文件名或文档标题提取）
        tags (str): 标签（逗号分隔，留空则 AI 自动生成）

    Returns:
        Dict[str, Any]: 导入结果，包含知识 ID、段落数、表格数等
    """
    try:
        from core.file_parser import DOCXParser
        from core.knowledge_store import add_knowledge
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")

    # 清理文件路径（去除空格、换行符和引号）
    file_path = file_path.strip().strip('"').strip("'")

    # 解析 DOCX
    parser = DOCXParser()
    if not parser.can_handle(file_path):
        raise ValueError(f"文件类型错误: {file_path} 不是 DOCX 文件")

    parsed = await parser.parse(file_path)

    # 构建来源信息
    source = f"DOCX 文档：{parsed['metadata']['file_path']}"

    # 使用解析出的标题或用户指定的标题
    final_title = title if title else parsed['title']

    # 添加到知识库
    result = await add_knowledge(
        content=parsed['content'],
        title=final_title,
        tags=tags,
        source=source
    )

    # 保存原始 DOCX 文件副本
    from core.knowledge_store import _save_attachment
    attachment_path = _save_attachment(
        base_id=result['id'],
        source_path=parsed['metadata']['file_path'],
        doc_type='docx'
    )

    # 添加 DOCX 特有的元数据
    result['docx_paragraphs'] = parsed['metadata']['paragraphs']
    result['docx_tables'] = parsed['metadata']['tables']
    result['original_path'] = parsed['metadata']['file_path']
    result['attachment_path'] = attachment_path if attachment_path else "未保存"

    return result


@YA_MCPServer_Tool(
    name="import_webpage",
    title="Import Webpage as Markdown Note",
    description="导入网页为 Markdown 笔记。自动抓取网页内容并转换为 Markdown 格式，支持技术博客、文档、文章等",
)
async def import_webpage(
    url: str,
    title: str = "",
    tags: str = "",
) -> Dict[str, Any]:
    """
    导入网页为 Markdown 笔记
    
    Args:
        url (str): 网页 URL（必须以 http:// 或 https:// 开头）
        title (str): 笔记标题（留空则从网页标题提取）
        tags (str): 标签（逗号分隔，留空则 AI 自动生成）
        
    Returns:
        Dict[str, Any]: 导入结果，包含知识 ID、URL、分块数等
    """
    try:
        from core.file_parser import WebPageParser
        from core.knowledge_store import add_knowledge
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    
    # 清理 URL（去除空格和换行符）
    url = url.strip()
    
    # 解析网页
    parser = WebPageParser()
    if not parser.can_handle(url):
        raise ValueError(f"URL 格式错误: {url}（需要以 http:// 或 https:// 开头）")
    
    parsed = await parser.parse(url)
    
    # 构建来源信息
    source = f"网页：{parsed['metadata']['url']}"
    
    # 使用解析出的标题或用户指定的标题
    final_title = title if title else parsed['title']
    
    # 添加到知识库
    result = await add_knowledge(
        content=parsed['content'],
        title=final_title,
        tags=tags,
        source=source
    )
    
    # 保存网页 HTML 快照（可选）
    from core.knowledge_store import _save_attachment
    from pathlib import Path
    
    # 将 HTML 内容保存为文件
    if 'html_content' in parsed['metadata']:
        temp_html_path = Path(f"./temp_{result['id']}.html")
        try:
            temp_html_path.write_text(parsed['metadata']['html_content'], encoding='utf-8')
            attachment_path = _save_attachment(
                base_id=result['id'],
                source_path=str(temp_html_path),
                doc_type='html'
            )
            result['html_snapshot'] = attachment_path if attachment_path else "未保存"
        finally:
            if temp_html_path.exists():
                temp_html_path.unlink()
    
    # 添加网页特有的元数据
    result['url'] = parsed['metadata']['url']
    
    return result


@YA_MCPServer_Tool(
    name="import_document",
    title="Import Document (Auto-detect Type)",
    description="智能导入文档到知识库，自动识别类型（PDF、PPTX、DOCX 或网页）并转换为 Markdown。支持本地文件和在线网页",
)
async def import_document(
    source: str,
    title: str = "",
    tags: str = "",
) -> Dict[str, Any]:
    """
    智能导入文档（自动识别类型）
    
    Args:
        source (str): 文档来源（PDF 文件路径 或 网页 URL）
        title (str): 标题（留空则自动提取）
        tags (str): 标签（逗号分隔，留空则 AI 自动生成）
        
    Returns:
        Dict[str, Any]: 导入结果
        
    Examples:
        >>> # 导入 PDF
        >>> import_document(source="./paper.pdf")
        
        >>> # 导入网页
        >>> import_document(source="https://example.com/article")
    """
    try:
        from core.file_parser import DocumentParserFactory
        from core.knowledge_store import add_knowledge
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    
    # 清理输入（去除空格和换行符）
    source = source.strip()
    
    # 自动选择解析器
    factory = DocumentParserFactory()
    parsed = await factory.parse(source)
    
    # 构建来源信息
    doc_type = parsed['metadata']['doc_type']
    if doc_type == 'pdf':
        source_info = f"PDF 文档：{parsed['metadata']['file_path']}"
    elif doc_type == 'pptx':
        source_info = f"PPTX 演示文稿：{parsed['metadata']['file_path']}"
    elif doc_type == 'docx':
        source_info = f"DOCX 文档：{parsed['metadata']['file_path']}"
    elif doc_type == 'webpage':
        source_info = f"网页：{parsed['metadata']['url']}"
    else:
        source_info = source
    
    # 使用解析出的标题或用户指定的标题
    final_title = title if title else parsed['title']
    
    # 添加到知识库
    result = await add_knowledge(
        content=parsed['content'],
        title=final_title,
        tags=tags,
        source=source_info
    )
    
    # 添加文档类型特有的元数据
    result['doc_type'] = doc_type
    result['metadata'] = parsed['metadata']
    
    return result
