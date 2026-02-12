"""
文本翻译工具，包括：
- text_translate: 多语言翻译
- get_supported_languages: 获取支持的语言
"""

from typing import Any, Dict
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="text_translate",
    title="Text Translate",
    description="多语言文本翻译，支持中英日韩法德西俄等语言互译，免费无需 Key",
)
async def text_translate(
    text: str,
    target_lang: str = "英文",
    source_lang: str = "auto",
) -> Dict[str, Any]:
    """翻译文本。

    Args:
        text (str): 要翻译的文本。
        target_lang (str): 目标语言，默认 "英文"。
        source_lang (str): 源语言，默认 "auto"。

    Returns:
        Dict[str, Any]: 翻译结果。
    """
    try:
        from core.translate_service import translate_text
    except ImportError as e:
        raise RuntimeError(f"无法导入翻译模块: {e}")

    return await translate_text(text=text, target_lang=target_lang, source_lang=source_lang)


@YA_MCPServer_Tool(
    name="get_supported_languages",
    title="Supported Languages",
    description="获取翻译支持的所有语言列表",
)
async def get_languages() -> Dict[str, str]:
    """获取支持的语言列表。"""
    try:
        from core.translate_service import get_supported_languages
    except ImportError as e:
        raise RuntimeError(f"无法导入翻译模块: {e}")

    return get_supported_languages()