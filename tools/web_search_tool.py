"""
网络搜索工具，包括：
- web_search: 使用 DuckDuckGo 搜索网络内容
- fetch_webpage: 获取网页完整内容
- search_with_content: 搜索并获取首个结果的完整内容
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
