"""
智能对话工具，包括：
- smart_chat: 调用 DeepSeek 进行对话
"""

from typing import Any, Dict, Optional
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="smart_chat",
    title="Smart Chat",
    description="调用 DeepSeek 大语言模型进行智能对话",
)
async def smart_chat(
    message: str,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """调用 DeepSeek 进行智能对话。

    Args:
        message (str): 用户消息。
        system_prompt (Optional[str]): 系统提示词。

    Returns:
        Dict[str, Any]: AI 回复和 Token 使用信息。
    """
    try:
        from core.llm_service import chat_with_llm
    except ImportError as e:
        raise RuntimeError(f"无法导入 LLM 模块: {e}")

    return await chat_with_llm(message=message, system_prompt=system_prompt)