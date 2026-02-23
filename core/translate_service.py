"""
文本翻译服务模块

提供以下功能：
- translate_text: 优先使用 LLM 翻译，失败时降级到 MyMemory 免费 API
- get_supported_languages: 获取支持的语言列表
"""

from typing import Dict, Any
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("translate_service")

LANGUAGE_MAP = {
    "中文": "zh-CN", "英文": "en", "日文": "ja", "韩文": "ko",
    "法文": "fr", "德文": "de", "西班牙文": "es", "俄文": "ru",
    "阿拉伯文": "ar", "葡萄牙文": "pt", "意大利文": "it",
    "chinese": "zh-CN", "english": "en", "japanese": "ja", "korean": "ko",
    "french": "fr", "german": "de", "spanish": "es", "russian": "ru",
}

_CODE_TO_NAME = {v: k for k, v in LANGUAGE_MAP.items()}


async def translate_text(
    text: str,
    target_lang: str = "英文",
    source_lang: str = "auto",
) -> Dict[str, Any]:
    """翻译文本。优先使用 LLM，失败时降级到 MyMemory。

    Args:
        text (str): 要翻译的文本。
        target_lang (str): 目标语言(如 "英文"、"中文"、"ja")，默认 "英文"。
        source_lang (str): 源语言，默认 "auto" 自动检测。

    Returns:
        Dict[str, Any]: 翻译结果，含 original、translated、source_lang、target_lang、method。
    """
    use_llm = get_config("translate.use_llm", True)
    mymemory_fallback = get_config("translate.mymemory_fallback", True)

    target_code = LANGUAGE_MAP.get(target_lang, target_lang)
    source_code = LANGUAGE_MAP.get(source_lang, source_lang) if source_lang != "auto" else "auto"

    if use_llm:
        try:
            return await _translate_with_llm(text, target_lang, target_code, source_lang, source_code)
        except Exception as e:
            logger.warning(f"LLM 翻译失败: {e}")
            if not mymemory_fallback:
                raise RuntimeError(f"LLM 翻译失败(已禁用 MyMemory 降级): {e}")
            logger.info("降级到 MyMemory 翻译")

    return await _translate_with_mymemory(text, target_code, source_code)


async def _translate_with_llm(
    text: str,
    target_lang_display: str,
    target_code: str,
    source_lang_display: str,
    source_code: str,
) -> Dict[str, Any]:
    """使用 LLM 翻译，返回纯翻译结果。"""
    from core.llm_service import chat_with_llm

    provider = get_config("translate.llm_provider", "deepseek")
    target_name = _CODE_TO_NAME.get(target_code, target_lang_display)
    source_hint = "" if source_code == "auto" else f"源语言是{_CODE_TO_NAME.get(source_code, source_lang_display)}，"

    system_prompt = (
        "你是一名专业翻译。请将用户提供的文本翻译成目标语言。"
        "只输出翻译结果，不要添加任何解释、注释或原文。"
    )
    user_msg = f"请将以下文本{source_hint}翻译成{target_name}：\n\n{text}"

    resp = await chat_with_llm(message=user_msg, system_prompt=system_prompt, provider=provider)
    translated = resp["reply"].strip()

    logger.info(f"LLM 翻译完成: {len(text)} 字 -> {len(translated)} 字")
    return {
        "original": text,
        "translated": translated,
        "source_lang": source_code,
        "target_lang": target_code,
        "method": f"llm:{resp['provider']}:{resp['model']}",
    }


async def _translate_with_mymemory(text: str, target_code: str, source_code: str) -> Dict[str, Any]:
    """使用 MyMemory 免费 API 翻译(降级方案)。"""
    import httpx

    base_url = get_config("translate.base_url", "https://api.mymemory.translated.net")
    mymemory_src = "autodetect" if source_code == "auto" else source_code

    try:
        params = {"q": text, "langpair": f"{mymemory_src}|{target_code}"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{base_url}/get", params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("responseStatus") != 200:
            raise RuntimeError(f"MyMemory API 错误: {data.get('responseDetails', '未知')}")

        return {
            "original": text,
            "translated": data["responseData"]["translatedText"],
            "source_lang": source_code,
            "target_lang": target_code,
            "method": "mymemory",
        }
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"MyMemory 翻译失败: {e}")


def get_supported_languages() -> Dict[str, str]:
    """获取支持的语言列表。"""
    return LANGUAGE_MAP.copy()