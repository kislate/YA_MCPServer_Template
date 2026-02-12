"""
RAG (Retrieval-Augmented Generation) 服务模块

提供以下功能：
- ask_knowledge: 检索知识库 + LLM 生成回答
"""

from typing import Dict, Any, Optional
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("rag_service")

RAG_SYSTEM_PROMPT = """你是一个专业的知识问答助手。基于以下检索到的知识内容回答问题。

## 规则：
1. 只基于提供的知识内容回答，不编造
2. 知识不足时明确告知用户
3. 标注信息来源
4. 条理清晰

## 检索到的知识：
{context}

如果以上知识不包含答案，回答"根据现有知识库暂无相关信息，建议添加相关知识后再次提问。"
"""


async def ask_knowledge(
    question: str,
    top_k: int = 5,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    基于知识库的 RAG 智能问答。

    流程: 语义检索知识片段 → 拼接为上下文 → LLM 生成回答

    Args:
        question (str): 用户问题。
        top_k (int): 检索片段数，默认 5。
        provider (Optional[str]): LLM 提供商。

    Returns:
        Dict[str, Any]: 回答 + 引用来源。

    Raises:
        RuntimeError: 如果流程失败。

    Example:
        {
            "question": "Python装饰器怎么用？",
            "answer": "根据知识库...",
            "sources": [{"title": "Python装饰器", "relevance": 0.85}],
            "context_chunks_used": 3
        }
    """
    logger.info(f"RAG 问答: '{question[:50]}'")

    try:
        from core.knowledge_store import search_knowledge
    except ImportError as e:
        raise RuntimeError(f"无法导入知识模块: {e}")

    try:
        search_results = await search_knowledge(query=question, top_k=top_k)
    except Exception as e:
        raise RuntimeError(f"知识检索失败: {e}")

    results = search_results.get("results", [])
    if not results:
        return {
            "question": question,
            "answer": "知识库中暂无相关内容，请先用 add_knowledge 添加知识。",
            "sources": [],
            "context_chunks_used": 0,
        }

    # 过滤低相关度
    min_rel = get_config("knowledge.retrieval.min_relevance", 0.3)
    filtered = [r for r in results if r.get("relevance", 0) >= min_rel] or results[:2]

    # 构建上下文
    context_parts, sources = [], []
    for i, r in enumerate(filtered):
        raw_info = f", 原始文件: {r['raw_file']}" if r.get('raw_file') else ""
        context_parts.append(
            f"【知识{i+1}】(来源: {r.get('title', '未知')}, 相关度: {r.get('relevance', 0):.2f}{raw_info})\n{r['content']}"
        )
        sources.append({
            "title": r.get("title", "未知"),
            "relevance": r.get("relevance", 0),
            "raw_file": r.get("raw_file", ""),
        })

    system_prompt = RAG_SYSTEM_PROMPT.format(context="\n\n---\n\n".join(context_parts))

    try:
        from core.llm_service import chat_with_llm
    except ImportError as e:
        raise RuntimeError(f"无法导入 LLM 模块: {e}")

    try:
        llm_resp = await chat_with_llm(message=question, system_prompt=system_prompt, provider=provider)
    except Exception as e:
        raise RuntimeError(f"LLM 生成失败: {e}")

    logger.info(f"RAG 完成，使用 {len(filtered)} 个片段")

    return {
        "question": question,
        "answer": llm_resp["reply"],
        "sources": sources,
        "llm_provider": llm_resp["provider"],
        "context_chunks_used": len(filtered),
        "token_usage": llm_resp["usage"],
    }
