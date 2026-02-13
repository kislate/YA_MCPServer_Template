"""
LLM 服务模块 - DeepSeek

提供以下功能：
- chat_with_llm: 调用 DeepSeek API 进行对话
- generate_metadata: 调用 AI 自动生成知识的标题、标签、来源类型
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("llm_service")

# 缓存 API key，避免每次调用都解密 SOPS
_cached_api_key: Optional[str] = None


async def chat_with_llm(
    message: str,
    system_prompt: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    调用 DeepSeek API 进行对话。

    Args:
        message (str): 用户消息。
        system_prompt (Optional[str]): 系统提示词。
        provider (Optional[str]): 保留参数，当前仅支持 "deepseek"。

    Returns:
        Dict[str, Any]: 对话结果，包含回复内容和 Token 使用信息。

    Raises:
        RuntimeError: 如果 API 调用失败。

    Example:
        {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "reply": "Python 的装饰器是...",
            "usage": {"prompt_tokens": 150, "completion_tokens": 200}
        }
    """
    provider = "deepseek"

    logger.info(f"调用 DeepSeek，消息长度: {len(message)}")

    try:
        api_key = await asyncio.to_thread(_get_api_key)
        base_url = get_config("llm.deepseek.base_url", "https://api.deepseek.com")
        model = get_config("llm.deepseek.model", "deepseek-chat")
        max_tokens = get_config("llm.deepseek.max_tokens", 2048)
        temperature = get_config("llm.deepseek.temperature", 0.7)
    except Exception as e:
        raise RuntimeError(f"读取 LLM 配置失败: {e}")

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        reply = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        }

        logger.info(f"DeepSeek 回复成功，Token: {usage}")

        return {
            "provider": provider,
            "model": model,
            "reply": reply,
            "usage": usage,
        }
    except Exception as e:
        raise RuntimeError(f"DeepSeek 调用失败: {e}")


def _get_api_key() -> str:
    """从 SOPS 获取 DeepSeek API Key，环境变量作为备用。结果缓存。"""
    global _cached_api_key
    if _cached_api_key:
        return _cached_api_key

    # 优先从 SOPS 获取
    try:
        from modules.YA_Secrets.secrets_parser import get_secret
        key = get_secret("deepseek_api_key")
        if key:
            logger.debug("从 SOPS 获取 DeepSeek API Key 成功")
            _cached_api_key = key
            return key
    except Exception as e:
        logger.warning(f"SOPS 获取 API Key 失败: {e}")

    # 备用：环境变量
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        logger.debug("从环境变量获取 DeepSeek API Key")
        return key

    raise RuntimeError(
        "未找到 DeepSeek API Key，请通过 SOPS 加密到 env.yaml 或设置环境变量 DEEPSEEK_API_KEY"
    )


METADATA_SYSTEM_PROMPT = """你是一个知识管理助手。根据用户提供的文本内容，生成以下元数据：

1. title: 简洁的中文标题（10字以内），概括文本主题
2. tags: 3-5个标签，用逗号分隔，反映文本的关键主题和领域（如 "Python,装饰器,编程"）
3. source: 文本来源类型，从以下选项中选择最合适的一个：课件、笔记、论文、教材、文档、博客、代码、其他

严格按以下 JSON 格式返回，不要包含其他内容：
{"title": "...", "tags": "...", "source": "..."}"""


async def generate_metadata(content: str) -> Dict[str, str]:
    """
    调用 DeepSeek 为知识内容自动生成 title、tags、source。

    Args:
        content (str): 知识原文（取前 1500 字送给 AI）。

    Returns:
        Dict[str, str]: {"title": "...", "tags": "...", "source": "..."}
    """
    # 截取前 1500 字，避免 token 过长
    preview = content[:1500]
    logger.info(f"AI 生成元数据，内容预览长度: {len(preview)}")

    try:
        api_key = await asyncio.to_thread(_get_api_key)
        base_url = get_config("llm.deepseek.base_url", "https://api.deepseek.com")
        model = get_config("llm.deepseek.model", "deepseek-chat")
    except Exception as e:
        raise RuntimeError(f"读取 LLM 配置失败: {e}")

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": METADATA_SYSTEM_PROMPT},
                {"role": "user", "content": f"请为以下内容生成元数据：\n\n{preview}"},
            ],
            max_tokens=200,
            temperature=0.3,
        )

        reply = response.choices[0].message.content.strip()
        # 尝试从回复中提取 JSON
        # 有时 AI 会返回 ```json ... ```，需要清理
        if "```" in reply:
            reply = reply.split("```")[1]
            if reply.startswith("json"):
                reply = reply[4:]
            reply = reply.strip()

        result = json.loads(reply)
        logger.info(f"AI 元数据生成成功: {result}")
        return {
            "title": result.get("title", "未命名"),
            "tags": result.get("tags", ""),
            "source": result.get("source", "用户笔记"),
        }
    except json.JSONDecodeError:
        logger.warning(f"AI 返回的 JSON 解析失败: {reply}")
        return {"title": "未命名", "tags": "", "source": "用户笔记"}
    except Exception as e:
        raise RuntimeError(f"AI 生成元数据失败: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  用户画像提取
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROFILE_EXTRACT_PROMPT = """你是用户画像分析助手。根据用户的提问和系统回答，提取用户特征。

分析以下内容，提取：
1. interests: 用户可能感兴趣的领域/技术（数组，0-3个）
2. level: 从提问方式推测的学习阶段（"初学者"/"进阶"/"高级"，不确定则留空）
3. preferences: 用户的偏好特点（数组，0-2个，如"喜欢代码示例"、"关注性能"）
4. topics: 本次对话涉及的具体话题（数组，1-3个关键词）

严格按 JSON 格式返回，不要包含其他内容：
{"interests": [...], "level": "", "preferences": [...], "topics": [...]}"""


async def extract_user_profile(question: str, answer: str) -> Dict[str, Any]:
    """
    从一次问答中提取用户特征。

    Args:
        question: 用户提问。
        answer: 系统回答。

    Returns:
        用户特征字典。
    """
    logger.debug(f"提取用户画像，问题: '{question[:50]}'")

    try:
        api_key = await asyncio.to_thread(_get_api_key)
        base_url = get_config("llm.deepseek.base_url", "https://api.deepseek.com")
        model = get_config("llm.deepseek.model", "deepseek-chat")
    except Exception as e:
        logger.warning(f"读取配置失败: {e}")
        return {}

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        # 截取避免 token 过长
        truncated_answer = answer[:800] if len(answer) > 800 else answer

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PROFILE_EXTRACT_PROMPT},
                {"role": "user", "content": f"用户提问：{question}\n\n系统回答：{truncated_answer}"},
            ],
            max_tokens=200,
            temperature=0.3,
        )

        reply = response.choices[0].message.content.strip()
        if "```" in reply:
            reply = reply.split("```")[1]
            if reply.startswith("json"):
                reply = reply[4:]
            reply = reply.strip()

        result = json.loads(reply)
        logger.info(f"用户画像提取: {result}")
        return result
    except json.JSONDecodeError:
        logger.warning(f"画像 JSON 解析失败: {reply}")
        return {}
    except Exception as e:
        logger.warning(f"用户画像提取失败: {e}")
        return {}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI 补充知识生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUPPLEMENT_PROMPT = """你是一个知识补充助手。用户刚刚提了一个问题，系统基于知识库给出了回答。
现在请你生成 1-2 条**补充知识**，这些知识应该：

1. 与用户问题相关但未被现有知识覆盖
2. 对用户后续学习有帮助（延伸、前置知识、易混淆概念等）
3. 每条 100-300 字，内容准确实用

{profile_context}

严格按 JSON 格式返回，不要包含其他内容：
[{{"title": "补充知识标题", "content": "知识内容", "tags": "标签1,标签2", "reason": "为什么推荐这条"}}]

如果没有值得补充的内容，返回空数组 []"""


async def generate_supplementary_knowledge(
    question: str,
    answer: str,
    existing_sources: List[str] = None,
    user_profile: Dict[str, Any] = None,
) -> List[Dict[str, str]]:
    """
    基于问答上下文生成补充知识。

    Args:
        question: 用户提问。
        answer: 系统回答。
        existing_sources: 已引用的知识标题列表。
        user_profile: 用户画像（用于个性化推荐）。

    Returns:
        补充知识列表。
    """
    logger.debug(f"生成补充知识，问题: '{question[:50]}'")

    # 构建用户画像上下文
    profile_context = ""
    if user_profile:
        interests = user_profile.get("interests", [])
        level = user_profile.get("level", "")
        if interests or level:
            parts = []
            if interests:
                parts.append(f"兴趣领域: {', '.join(interests)}")
            if level:
                parts.append(f"学习阶段: {level}")
            profile_context = f"用户画像：{'; '.join(parts)}。请据此调整补充知识的深度和方向。"

    try:
        api_key = await asyncio.to_thread(_get_api_key)
        base_url = get_config("llm.deepseek.base_url", "https://api.deepseek.com")
        model = get_config("llm.deepseek.model", "deepseek-chat")
    except Exception as e:
        logger.warning(f"读取配置失败: {e}")
        return []

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        user_msg = f"用户提问：{question}\n\n系统回答（摘要）：{answer[:600]}"
        if existing_sources:
            user_msg += f"\n\n已引用的知识：{', '.join(existing_sources)}"

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SUPPLEMENT_PROMPT.format(profile_context=profile_context)},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=800,
            temperature=0.5,
        )

        reply = response.choices[0].message.content.strip()
        if "```" in reply:
            reply = reply.split("```")[1]
            if reply.startswith("json"):
                reply = reply[4:]
            reply = reply.strip()

        result = json.loads(reply)
        if isinstance(result, list):
            logger.info(f"补充知识生成: {len(result)} 条")
            return result
        return []
    except json.JSONDecodeError:
        logger.warning(f"补充知识 JSON 解析失败: {reply}")
        return []
    except Exception as e:
        logger.warning(f"补充知识生成失败: {e}")
        return []