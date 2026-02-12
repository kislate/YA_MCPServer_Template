"""
文本翻译服务模块

提供以下功能：
- translate_text: 使用 MyMemory 免费 API 进行多语言翻译
- get_supported_languages: 获取支持的语言列表
"""

from typing import Dict, Any
import httpx
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("translate_service")

LANGUAGE_MAP = {
    "中文": "zh-CN", "英文": "en", "日文": "ja", "韩文": "ko",
    "法文": "fr", "德文": "de", "西班牙文": "es", "俄文": "ru",
    "chinese": "zh-CN", "english": "en", "japanese": "ja", "korean": "ko",
    "french": "fr", "german": "de", "spanish": "es", "russian": "ru",
}


async def translate_text(
    text: str,
    target_lang: str = "英文",
    source_lang: str = "auto",
) -> Dict[str, Any]:
    """
    使用 MyMemory API 进行文本翻译（免费，无需 Key）。

    Args:
        text (str): 要翻译的文本。
        target_lang (str): 目标语言（如 "英文"、"中文"、"ja"），默认 "英文"。
        source_lang (str): 源语言，默认 "auto" 自动检测。

    Returns:
        Dict[str, Any]: 翻译结果。

    Raises:
        RuntimeError: 如果翻译失败。

    Example:
        {
            "original": "你好世界",
            "translated": "Hello World",
            "source_lang": "zh-CN",
            "target_lang": "en"
        }
    """
    logger.info(f"翻译: '{text[:50]}' -> {target_lang}")

    target_code = LANGUAGE_MAP.get(target_lang, target_lang)
    source_code = LANGUAGE_MAP.get(source_lang, source_lang) if source_lang != "auto" else "autodetect"

    try:
        params = {
            "q": text,
            "langpair": f"{source_code}|{target_code}",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://api.mymemory.translated.net/get", params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("responseStatus") != 200:
            raise RuntimeError(f"翻译 API 错误: {data.get('responseDetails', '未知')}")

        return {
            "original": text,
            "translated": data["responseData"]["translatedText"],
            "source_lang": source_code,
            "target_lang": target_code,
        }
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"翻译失败: {e}")


def get_supported_languages() -> Dict[str, str]:
    """获取支持的语言列表。"""
    return LANGUAGE_MAP.copy()