"""
文档处理模块

提供以下功能：
- split_text: 将长文本按固定大小切分为多个片段（支持重叠）
"""

from typing import List
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("document_processor")


def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[str]:
    """
    将长文本切分为多个片段。

    在句号、换行符等自然断点处优先切分。

    Args:
        text (str): 要切分的文本。
        chunk_size (int): 每个片段最大字符数，默认 500。
        chunk_overlap (int): 相邻片段重叠字符数，默认 50。

    Returns:
        List[str]: 切分后的文本片段列表。

    Raises:
        ValueError: 如果参数不合法。

    Example:
        >>> split_text("一段很长的文本...", chunk_size=100)
        ["一段很长的...", "...的文本接下来..."]
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size 必须大于 0，当前: {chunk_size}")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(f"chunk_overlap ({chunk_overlap}) 必须在 [0, {chunk_size}) 范围内")

    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    break_chars = ["\n\n", "\n", "。", "！", "？", ". ", "! ", "? ", "；"]
    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # 在后半段寻找自然断点
        best_break = -1
        for bc in break_chars:
            pos = text.rfind(bc, start + chunk_size // 2, end)
            if pos > best_break:
                best_break = pos + len(bc)

        if best_break > start:
            end = best_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - chunk_overlap

    logger.debug(f"文本分块: 原始={len(text)}字, 片段数={len(chunks)}")
    return chunks
