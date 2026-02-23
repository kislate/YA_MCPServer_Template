"""
文档导入工具，包括：
- import_pdf: 导入 PDF 文档
- import_pptx: 导入 PPTX 演示文稿
- import_docx: 导入 DOCX Word 文档
- import_webpage: 导入网页笔记
- import_document: 通用文档导入（自动识别类型）
- batch_import_documents: 批量导入整个文件夹
"""

from pathlib import Path
from typing import Any, Dict, List
from tools import YA_MCPServer_Tool


# ──────────────────────────────────────────────
# 内部公共管道：parse完成后统一执行 add/attach/summary
# ──────────────────────────────────────────────

async def _run_import_pipeline(parsed: Dict[str, Any], title: str, tags: str, summarize: bool = True) -> Dict[str, Any]:
    """
    文档导入公共管道：add_knowledge → _save_attachment → summarize_content。
    所有 import_* 工具共用此逻辑，避免重复代码。
    summarize=False 时跳过 AI 摘要生成，速度更快。
    """
    from core.knowledge_store import add_knowledge, _save_attachment
    from core.llm_service import summarize_content

    doc_type = parsed["metadata"]["doc_type"]

    # 构建来源字符串
    source_map = {
        "pdf":     lambda m: f"PDF 文档：{m['file_path']}",
        "pptx":    lambda m: f"PPTX 演示文稿：{m['file_path']}",
        "docx":    lambda m: f"DOCX 文档：{m['file_path']}",
        "webpage": lambda m: f"网页：{m['url']}",
    }
    source_info = source_map.get(doc_type, lambda m: m.get("file_path", ""))(parsed["metadata"])

    final_title = title if title else parsed["title"]

    result = await add_knowledge(
        content=parsed["content"],
        title=final_title,
        tags=tags,
        source=source_info,
    )

    # 保存原始文件 / HTML 快照
    attachment_path = ""
    if doc_type in ("pdf", "pptx", "docx"):
        attachment_path = _save_attachment(
            base_id=result["id"],
            source_path=parsed["metadata"]["file_path"],
            doc_type=doc_type,
        )
    elif doc_type == "webpage" and parsed["metadata"].get("html_content"):
        temp_html = Path(f"./temp_{result['id']}.html")
        try:
            temp_html.write_text(parsed["metadata"]["html_content"], encoding="utf-8")
            attachment_path = _save_attachment(
                base_id=result["id"],
                source_path=str(temp_html),
                doc_type="html",
            )
        finally:
            if temp_html.exists():
                temp_html.unlink()

    result["attachment_path"] = attachment_path or "未保存"
    result["doc_type"] = doc_type

    # 文档类型专属元数据
    if doc_type == "pdf":
        result["pdf_pages"] = parsed["metadata"]["pages"]
        result["original_path"] = parsed["metadata"]["file_path"]
    elif doc_type == "pptx":
        result["pptx_slides"] = parsed["metadata"]["slides"]
        result["original_path"] = parsed["metadata"]["file_path"]
    elif doc_type == "docx":
        result["docx_paragraphs"] = parsed["metadata"]["paragraphs"]
        result["docx_tables"] = parsed["metadata"]["tables"]
        result["original_path"] = parsed["metadata"]["file_path"]
    elif doc_type == "webpage":
        result["url"] = parsed["metadata"]["url"]

    # AI 摘要（可选）
    if summarize:
        try:
            summary = await summarize_content(parsed["content"], final_title)
            if summary:
                result["ai_summary"] = summary
        except Exception as e:
            result["ai_summary"] = f"摘要生成失败: {e}"
    else:
        result["ai_summary"] = "已跳过"

    return result


# ──────────────────────────────────────────────
# 各格式入口（薄包装）
# ──────────────────────────────────────────────

@YA_MCPServer_Tool(
    name="import_pdf",
    title="Import PDF Document",
    description="导入 PDF 文档到知识库。自动提取文本内容，按页面分块建立向量索引。支持学术论文、课件、电子书等。summarize=False 可跳过 AI 摘要以加快速度",
)
async def import_pdf(file_path: str, title: str = "", tags: str = "", summarize: bool = True) -> Dict[str, Any]:
    """导入 PDF 文档到知识库。Args: file_path, title, tags, summarize."""
    from core.file_parser import PDFParser
    file_path = file_path.strip().strip('"').strip("'")
    parser = PDFParser()
    if not parser.can_handle(file_path):
        raise ValueError(f"文件类型错误: {file_path} 不是 PDF 文件")
    return await _run_import_pipeline(await parser.parse(file_path), title, tags, summarize)


@YA_MCPServer_Tool(
    name="import_pptx",
    title="Import PPTX Presentation",
    description="导入 PPTX 演示文稿到知识库。自动提取幻灯片文本和表格内容，转换为 Markdown 格式建立向量索引。支持课件、报告、培训材料等。summarize=False 可跳过 AI 摘要以加快速度",
)
async def import_pptx(file_path: str, title: str = "", tags: str = "", summarize: bool = True) -> Dict[str, Any]:
    """导入 PPTX 演示文稿到知识库。Args: file_path, title, tags, summarize."""
    from core.file_parser import PPTXParser
    file_path = file_path.strip().strip('"').strip("'")
    parser = PPTXParser()
    if not parser.can_handle(file_path):
        raise ValueError(f"文件类型错误: {file_path} 不是 PPTX 文件")
    return await _run_import_pipeline(await parser.parse(file_path), title, tags, summarize)


@YA_MCPServer_Tool(
    name="import_docx",
    title="Import DOCX Document",
    description="导入 DOCX Word 文档到知识库。自动提取段落、标题和表格内容，保留文档结构转换为 Markdown 格式。支持报告、论文、手册等。summarize=False 可跳过 AI 摘要以加快速度",
)
async def import_docx(file_path: str, title: str = "", tags: str = "", summarize: bool = True) -> Dict[str, Any]:
    """导入 DOCX Word 文档到知识库。Args: file_path, title, tags, summarize."""
    from core.file_parser import DOCXParser
    file_path = file_path.strip().strip('"').strip("'")
    parser = DOCXParser()
    if not parser.can_handle(file_path):
        raise ValueError(f"文件类型错误: {file_path} 不是 DOCX 文件")
    return await _run_import_pipeline(await parser.parse(file_path), title, tags, summarize)


@YA_MCPServer_Tool(
    name="import_webpage",
    title="Import Webpage as Markdown Note",
    description="导入网页为 Markdown 笔记。自动抓取网页内容并转换为 Markdown 格式，支持技术博客、文档、文章等。summarize=False 可跳过 AI 摘要以加快速度",
)
async def import_webpage(url: str, title: str = "", tags: str = "", summarize: bool = True) -> Dict[str, Any]:
    """导入网页为 Markdown 笔记。Args: url, title, tags, summarize."""
    from core.file_parser import WebPageParser
    url = url.strip()
    parser = WebPageParser()
    if not parser.can_handle(url):
        raise ValueError(f"URL 格式错误: {url}（需要以 http:// 或 https:// 开头）")
    return await _run_import_pipeline(await parser.parse(url), title, tags, summarize)


@YA_MCPServer_Tool(
    name="import_document",
    title="Import Document (Auto-detect Type)",
    description="智能导入文档到知识库，自动识别类型（PDF、PPTX、DOCX 或网页）并转换为 Markdown。支持本地文件和在线网页。summarize=False 可跳过 AI 摘要以加快速度",
)
async def import_document(source: str, title: str = "", tags: str = "", summarize: bool = True) -> Dict[str, Any]:
    """智能导入文档（自动识别类型）。Args: source（文件路径或 URL）, title, tags, summarize."""
    from core.file_parser import DocumentParserFactory
    source = source.strip().strip('"').strip("'")
    parsed = await DocumentParserFactory().parse(source)
    return await _run_import_pipeline(parsed, title, tags, summarize)


@YA_MCPServer_Tool(
    name="batch_import_documents",
    title="Batch Import Documents",
    description="批量导入整个文件夹内的文档（PDF、PPTX、DOCX）到知识库。支持递归子目录，可按文件类型过滤。summarize=False 可跳过 AI 摘要显著提升批量导入速度",
)
async def batch_import_documents(
    folder_path: str,
    tags: str = "",
    recursive: bool = False,
    file_types: str = "",
    summarize: bool = True,
) -> Dict[str, Any]:
    """批量导入文件夹中的文档。

    Args:
        folder_path (str): 文件夹路径（绝对或相对）。
        tags (str): 为所有导入文档附加的标签（逗号分隔）。
        recursive (bool): 是否递归扫描子文件夹，默认 False。
        file_types (str): 限定格式，如 "pdf,docx"；留空则导入所有支持格式（pdf/pptx/docx）。
        summarize (bool): 是否生成 AI 摘要，默认 True。批量导入时建议设为 False 以提升速度。

    Returns:
        Dict[str, Any]: 汇总结果，包含成功列表和失败列表。
    """
    from core.file_parser import DocumentParserFactory

    folder = Path(folder_path.strip().strip('"').strip("'"))
    if not folder.is_dir():
        raise ValueError(f"路径不是有效文件夹: {folder_path}")

    supported = {".pdf", ".pptx", ".docx"}
    if file_types:
        requested = {f".{t.strip().lower()}" for t in file_types.split(",") if t.strip()}
        supported = supported & requested
        if not supported:
            raise ValueError(f"file_types 中没有支持的格式（支持：pdf, pptx, docx）")

    pattern = "**/*" if recursive else "*"
    files = sorted(f for f in folder.glob(pattern) if f.is_file() and f.suffix.lower() in supported)

    if not files:
        return {"total": 0, "succeeded": [], "failed": [], "message": "未找到符合条件的文件"}

    factory = DocumentParserFactory()
    succeeded: List[Dict] = []
    failed: List[Dict] = []

    for f in files:
        try:
            parsed = await factory.parse(str(f))
            r = await _run_import_pipeline(parsed, title="", tags=tags, summarize=summarize)
            succeeded.append({"file": f.name, "id": r["id"], "title": r["title"]})
        except Exception as e:
            failed.append({"file": f.name, "error": str(e)})

    return {
        "total": len(files),
        "succeeded_count": len(succeeded),
        "failed_count": len(failed),
        "succeeded": succeeded,
        "failed": failed,
    }
