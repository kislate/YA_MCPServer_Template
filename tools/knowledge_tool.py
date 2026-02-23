"""
知识管理工具，包括：
- add_knowledge: 添加知识
- search_knowledge: 语义搜索
- list_knowledge: 列出知识
- delete_knowledge: 删除知识
"""

from typing import Any, Dict
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="add_knowledge",
    title="Add Knowledge",
    description="添加知识到个人知识库，支持笔记、文档、课件等。自动分块建立向量索引，保存原始 Markdown。title/tags/source 留空则 AI 自动生成",
)
async def add_knowledge(
    content: str, title: str = "", tags: str = "", source: str = "",
) -> Dict[str, Any]:
    """添加知识到向量数据库。

    Args:
        content (str): 知识内容（Markdown 或纯文本）。
        title (str): 标题（留空则 AI 自动生成）。
        tags (str): 标签（逗号分隔，留空则 AI 自动生成）。
        source (str): 来源（留空则 AI 自动生成）。
    Returns:
        Dict[str, Any]: 添加结果，包含原始文件路径。
    """
    try:
        from core.knowledge_store import add_knowledge as _add
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _add(content=content, title=title, tags=tags, source=source)


@YA_MCPServer_Tool(
    name="search_knowledge",
    title="Search Knowledge",
    description="语义搜索知识库，基于语义相似度而非关键词匹配，返回结果包含原始 Markdown 文件路径",
)
async def search_knowledge(
    query: str, top_k: int = 5, tag_filter: str = "",
) -> Dict[str, Any]:
    """语义搜索知识库。

    Args:
        query (str): 搜索内容（自然语言）。
        top_k (int): 返回前 K 条。
        tag_filter (str): 标签过滤。
    Returns:
        Dict[str, Any]: 搜索结果。
    """
    try:
        from core.knowledge_store import search_knowledge as _search
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _search(query=query, top_k=top_k, tag_filter=tag_filter)


@YA_MCPServer_Tool(
    name="list_knowledge",
    title="List Knowledge",
    description="列出知识库中的所有知识条目（最多 100 个）",
)
async def list_knowledge(tag_filter: str = "", limit: int = 100) -> Dict[str, Any]:
    """列出知识。

    Args:
        tag_filter (str): 标签过滤。
        limit (int): 最大数量（默认 100）。
    Returns:
        Dict[str, Any]: 知识列表。
    """
    try:
        from core.knowledge_store import list_knowledge as _list
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _list(tag_filter=tag_filter, limit=limit)


@YA_MCPServer_Tool(
    name="get_knowledge",
    title="Get Knowledge Markdown",
    description="获取指定 ID 笔记的 Markdown 原文。若该笔记有原始附件（PDF、DOCX 等），在附录中标注文件名、格式、大小和路径",
)
async def get_knowledge(knowledge_id: str) -> Dict[str, Any]:
    """获取知识原始 Markdown 内容。

    Args:
        knowledge_id (str): 知识 ID（如 kb_09572213）。
    Returns:
        Dict[str, Any]: 包含 markdown 原文字段，以及 attachment 附件信息（若有）。
    """
    try:
        from core.knowledge_store import get_knowledge as _get
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _get(knowledge_id=knowledge_id)


@YA_MCPServer_Tool(
    name="delete_knowledge",
    title="Delete Knowledge",
    description="删除指定的知识条目",
)
async def delete_knowledge(knowledge_id: str) -> Dict[str, str]:
    """删除知识。

    Args:
        knowledge_id (str): 知识 ID。
    Returns:
        Dict[str, str]: 删除结果。
    """
    try:
        from core.knowledge_store import delete_knowledge as _del
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _del(knowledge_id=knowledge_id)
