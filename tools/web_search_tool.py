"""
网络搜索工具，包括：
- web_search: 使用 DuckDuckGo 搜索网络内容
- fetch_webpage: 获取网页完整内容
- search_with_content: 搜索并获取首个结果的完整内容
- search_and_save: 搜索网络并将结果存入知识库
"""

from typing import Any, Dict, List
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="web_search",
    title="Web Search",
    description="使用 DuckDuckGo 搜索网络内容，免费无需 API Key，支持全球搜索",
)
async def web_search(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
) -> Dict[str, Any]:
    """网络搜索工具。

    Args:
        query (str): 搜索关键词或问题。
        max_results (int): 返回结果数量，默认 5，最多 20。
        region (str): 搜索区域，默认 "wt-wt"（全球）。可选：wt-wt, cn-zh, us-en 等（注意：某些区域可能返回空结果）。

    Returns:
        Dict[str, Any]: 包含搜索结果列表，每个结果含 rank、title、url、snippet。
    """
    try:
        from core.web_search_service import duckduckgo_search
    except ImportError as e:
        raise RuntimeError(f"无法导入网络搜索模块: {e}")
    
    # 限制最大结果数
    max_results = min(max_results, 20)
    
    results = await duckduckgo_search(
        query=query,
        max_results=max_results,
        region=region
    )
    
    return {
        "query": query,
        "total": len(results),
        "results": results
    }


@YA_MCPServer_Tool(
    name="fetch_webpage",
    title="Fetch Webpage Content",
    description="获取指定网页的完整文本内容，自动提取正文并去除广告、导航等无关内容",
)
async def fetch_webpage(
    url: str,
    timeout: int = 10,
    extract_main_content: bool = True,
) -> Dict[str, Any]:
    """获取网页内容工具。

    Args:
        url (str): 网页地址（必须以 http:// 或 https:// 开头）。
        timeout (int): 请求超时时间（秒），默认 10。
        extract_main_content (bool): 是否提取主要内容（去除导航、广告等），默认 True。

    Returns:
        Dict[str, Any]: 包含 url、title、content、length 的网页信息。
    """
    try:
        from core.web_search_service import fetch_webpage_content
    except ImportError as e:
        raise RuntimeError(f"无法导入网络搜索模块: {e}")
    
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL 必须以 http:// 或 https:// 开头")
    
    return await fetch_webpage_content(
        url=url,
        timeout=timeout,
        extract_main_content=extract_main_content
    )


@YA_MCPServer_Tool(
    name="search_with_content",
    title="Search and Fetch Content",
    description="搜索网络并自动获取排名第一的网页完整内容，适合需要深度了解某个主题的场景",
)
async def search_with_content(
    query: str,
    max_results: int = 3,
) -> Dict[str, Any]:
    """搜索并获取内容工具。

    Args:
        query (str): 搜索关键词或问题。
        max_results (int): 搜索结果数量，默认 3。

    Returns:
        Dict[str, Any]: 包含搜索结果列表和第一个结果的完整网页内容。
    """
    try:
        from core.web_search_service import search_and_summarize
    except ImportError as e:
        raise RuntimeError(f"无法导入网络搜索模块: {e}")
    
    return await search_and_summarize(
        query=query,
        max_results=max_results,
        fetch_content=True
    )


@YA_MCPServer_Tool(
    name="search_and_save",
    title="Search and Save to Knowledge Base",
    description="搜索网络内容并自动存入知识库。可指定存几条结果，每条网页内容单独保存为知识条目，自动生成标题和标签",
)
async def search_and_save(
    query: str,
    max_results: int = 3,
    tags: str = "",
    save_all: bool = False,
) -> Dict[str, Any]:
    """搜索并存入知识库。

    Args:
        query (str): 搜索关键词或问题。
        max_results (int): 抓取并保存的结果数量，默认 3，最多 10。
        tags (str): 为保存的知识添加的标签（逗号分隔，留空则 AI 自动生成）。
        save_all (bool): True=保存所有结果；False（默认）=仅保存成功抓取到正文的结果。

    Returns:
        Dict[str, Any]: 汇总结果，包含每条保存的知识 ID 和标题。
    """
    from core.web_search_service import duckduckgo_search, fetch_webpage_content
    from core.knowledge_store import add_knowledge

    max_results = min(max_results, 10)
    search_items = await duckduckgo_search(query=query, max_results=max_results)

    if not search_items:
        return {"query": query, "total_searched": 0, "saved": [], "failed": [], "message": "搜索无结果"}

    saved: List[Dict] = []
    failed: List[Dict] = []

    for item in search_items:
        url = item.get("url", "")
        title_hint = item.get("title", "")
        snippet = item.get("snippet", "")

        # 尝试获取完整网页内容
        content = ""
        try:
            page = await fetch_webpage_content(url=url, timeout=10, extract_main_content=True)
            content = page.get("content", "").strip()
        except Exception as e:
            if not save_all:
                failed.append({"url": url, "title": title_hint, "error": f"抓取失败: {e}"})
                continue
            # save_all=True 时用 snippet 兜底
            content = snippet

        if not content:
            if not save_all:
                failed.append({"url": url, "title": title_hint, "error": "内容为空"})
                continue
            content = snippet or title_hint

        source_info = f"网页：{url}"
        try:
            result = await add_knowledge(
                content=content,
                title="",           # AI 自动生成
                tags=tags,
                source=source_info,
            )
            saved.append({
                "id": result["id"],
                "title": result["title"],
                "url": url,
                "chunks_count": result["chunks_count"],
            })
        except Exception as e:
            failed.append({"url": url, "title": title_hint, "error": f"保存失败: {e}"})

    return {
        "query": query,
        "total_searched": len(search_items),
        "saved_count": len(saved),
        "failed_count": len(failed),
        "saved": saved,
        "failed": failed,
    }
