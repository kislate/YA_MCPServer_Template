"""
记忆库管理工具，包括：
- memory_stats: 记忆库 + 用户画像统计
- list_memories: 列出记忆库条目
- clear_memories: 清空记忆库
"""

from typing import Any, Dict
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="memory_stats",
    title="Memory Stats",
    description="查看记忆库和用户画像统计：记忆条目数、容量使用率、用户兴趣、常用话题",
)
async def memory_stats() -> Dict[str, Any]:
    """获取记忆库统计信息。"""
    try:
        from core.memory_store import get_memory_stats
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await get_memory_stats()


@YA_MCPServer_Tool(
    name="list_memories",
    title="List Memories",
    description="列出记忆库中的所有 AI 补充知识条目，包括标题、标签、置信度、命中次数",
)
async def list_memories(limit: int = 20) -> Dict[str, Any]:
    """列出记忆条目。

    Args:
        limit (int): 最大返回数。
    Returns:
        Dict[str, Any]: 记忆列表。
    """
    try:
        from core.memory_store import list_memories as _list
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _list(limit=limit)


@YA_MCPServer_Tool(
    name="clear_memories",
    title="Clear Memories",
    description="清空记忆库（AI 补充知识），用户画像不受影响",
)
async def clear_memories() -> Dict[str, str]:
    """清空记忆库。"""
    try:
        from core.memory_store import clear_memories as _clear
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _clear()
