"""
网络搜索服务，包括：
- DuckDuckGo 搜索
- 网页内容提取
"""

import httpx
from typing import List, Dict, Any, Optional
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("web_search_service")


async def duckduckgo_search(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt"  # wt-wt = 全球搜索，经测试其他区域可能返回空结果
) -> List[Dict[str, Any]]:
    """
    使用 DuckDuckGo 进行网络搜索（免费，无需 API Key）
    
    Args:
        query: 搜索关键词
        max_results: 返回结果数量，默认 5
        region: 搜索区域，默认 wt-wt (全球)。注意：某些区域代码可能返回空结果
        
    Returns:
        搜索结果列表，每个结果包含 title、url、snippet
    """
    def _sync_search():
        """同步搜索函数，在单独线程中运行以避免 asyncio 冲突"""
        from ddgs import DDGS
        
        results = []
        with DDGS() as ddgs:
            # 注意：新版本中第一个参数是位置参数，不要使用 keywords=
            search_results = ddgs.text(
                query,
                region=region,
                max_results=max_results
            )
            
            # 先转换为列表，避免生成器问题
            results_list = list(search_results)
            
            for idx, result in enumerate(results_list, 1):
                results.append({
                    "rank": idx,
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                })
        
        return results
    
    try:
        import asyncio
        
        logger.info(f"DuckDuckGo 搜索: {query}, 最多 {max_results} 条结果")
        
        # 在单独的线程中运行同步代码，避免 asyncio 事件循环冲突
        results = await asyncio.to_thread(_sync_search)
        
        logger.info(f"找到 {len(results)} 条搜索结果")
        return results
        
    except ImportError:
        raise RuntimeError(
            "需要安装 ddgs 库: pip install ddgs (或 uv sync)"
        )
    except Exception as e:
        logger.error(f"DuckDuckGo 搜索失败: {e}")
        raise RuntimeError(f"搜索失败: {str(e)}")


async def fetch_webpage_content(
    url: str,
    timeout: int = 10,
    extract_main_content: bool = True
) -> Dict[str, Any]:
    """
    获取网页内容并提取主要文本
    
    Args:
        url: 网页地址
        timeout: 超时时间（秒），默认 10
        extract_main_content: 是否提取主要内容（去除导航、广告等），默认 True
        
    Returns:
        包含 url、title、content、length 的字典
    """
    try:
        logger.info(f"抓取网页: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            html_content = response.text
            
            if extract_main_content:
                # 使用 trafilatura 提取主要内容
                try:
                    import trafilatura
                    
                    extracted = trafilatura.extract(
                        html_content,
                        include_comments=False,
                        include_tables=True,
                        no_fallback=False
                    )
                    
                    if extracted:
                        content = extracted
                    else:
                        # 如果 trafilatura 提取失败，使用基础方法
                        content = _extract_with_bs4(html_content)
                        
                except ImportError:
                    logger.warning("未安装 trafilatura，使用基础提取方法")
                    content = _extract_with_bs4(html_content)
            else:
                content = _extract_with_bs4(html_content)
            
            # 获取标题
            title = _extract_title(html_content)
            
            result = {
                "url": url,
                "title": title,
                "content": content.strip(),
                "length": len(content)
            }
            
            logger.info(f"网页抓取成功，内容长度: {len(content)} 字符")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"网页请求失败: {e}")
        raise RuntimeError(f"无法访问网页: {str(e)}")
    except Exception as e:
        logger.error(f"网页内容提取失败: {e}")
        raise RuntimeError(f"内容提取失败: {str(e)}")


def _extract_with_bs4(html: str) -> str:
    """使用 BeautifulSoup 提取文本内容"""
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 移除脚本和样式
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # 获取文本
        text = soup.get_text(separator="\n", strip=True)
        
        # 清理多余空行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
        
    except ImportError:
        raise RuntimeError("需要安装 beautifulsoup4: pip install beautifulsoup4")


def _extract_title(html: str) -> str:
    """提取网页标题"""
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")
        
        return title_tag.get_text(strip=True) if title_tag else "无标题"
        
    except Exception:
        return "无标题"


async def search_and_summarize(
    query: str,
    max_results: int = 3,
    fetch_content: bool = False
) -> Dict[str, Any]:
    """
    搜索并可选择性地获取网页内容
    
    Args:
        query: 搜索关键词
        max_results: 返回结果数量
        fetch_content: 是否获取完整网页内容
        
    Returns:
        包含搜索结果和可选网页内容的字典
    """
    # 执行搜索
    search_results = await duckduckgo_search(query, max_results)
    
    if fetch_content and search_results:
        # 获取第一个结果的完整内容
        first_url = search_results[0]["url"]
        try:
            webpage_content = await fetch_webpage_content(first_url)
            return {
                "search_results": search_results,
                "top_content": webpage_content
            }
        except Exception as e:
            logger.warning(f"获取网页内容失败: {e}")
            return {
                "search_results": search_results,
                "top_content": None,
                "error": str(e)
            }
    
    return {
        "search_results": search_results
    }
