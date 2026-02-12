"""
RAG 智能问答工具，包括：
- ask_knowledge: 基于知识库的智能问答
- knowledge_stats: 知识库统计
"""

from typing import Any, Dict, Optional
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="ask_knowledge",
    title="Ask Knowledge (RAG)",
    description="基于知识库的智能问答：自动检索相关知识 + 大模型生成回答 + 标注来源",
)
async def ask_knowledge(
    question: str, top_k: int = 5, provider: Optional[str] = None,
) -> Dict[str, Any]:
    """RAG 智能问答。

    Args:
        question (str): 你的问题。
        top_k (int): 检索片段数。
        provider (Optional[str]): LLM 提供商。
    Returns:
        Dict[str, Any]: 回答 + 引用来源。
    """
    try:
        from core.rag_service import ask_knowledge as _ask
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _ask(question=question, top_k=top_k, provider=provider)


@YA_MCPServer_Tool(
    name="knowledge_stats",
    title="Knowledge Stats",
    description="获取知识库统计信息：条目数、标签分布、来源分布",
)
async def knowledge_stats() -> Dict[str, Any]:
    """获取统计信息。"""
    try:
        from core.knowledge_store import get_stats
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await get_stats()
