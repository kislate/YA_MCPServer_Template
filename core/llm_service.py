"""
LLM 服务模块 - 支持多 Provider

提供以下功能：
- chat_with_llm: 调用 LLM API 进行对话（支持 deepseek / openai / siliconflow）
- generate_metadata: 调用 AI 自动生成知识的标题、标签、来源类型
- summarize_content: 调用 AI 对文档内容生成结构化摘要总结
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("llm_service")

# 每个 provider 的 API Key 缓存
_api_key_cache: Dict[str, str] = {}

# 每个 provider 的默认配置
_PROVIDER_DEFAULTS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "env_var": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "env_var": "OPENAI_API_KEY",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3",
        "env_var": "SILICONFLOW_API_KEY",
    },
}


def _get_api_key_for_provider(provider: str) -> str:
    """获取指定 provider 的 API Key，优先 SOPS，其次环境变量。结果按 provider 缓存。"""
    if provider in _api_key_cache:
        return _api_key_cache[provider]

    sops_key_name = f"{provider}_api_key"
    env_var = _PROVIDER_DEFAULTS.get(provider, {}).get("env_var", f"{provider.upper()}_API_KEY")

    # 优先 SOPS
    try:
        from modules.YA_Secrets.secrets_parser import get_secret
        key = get_secret(sops_key_name)
        if key:
            logger.debug(f"从 SOPS 获取 {provider} API Key 成功")
            _api_key_cache[provider] = key
            return key
    except Exception as e:
        logger.warning(f"SOPS 获取 {provider} API Key 失败: {e}")

    # 备用：环境变量
    key = os.environ.get(env_var)
    if key:
        logger.debug(f"从环境变量 {env_var} 获取 {provider} API Key")
        _api_key_cache[provider] = key
        return key

    raise RuntimeError(
        f"未找到 {provider} API Key，请将其加密到 env.yaml（key: {sops_key_name}）或设置环境变量 {env_var}"
    )


def _get_provider_config(provider: str) -> Dict[str, Any]:
    """从 config.yaml 和内置默认值获取 provider 配置。"""
    defaults = _PROVIDER_DEFAULTS.get(provider, {})
    return {
        "base_url": get_config(f"llm.{provider}.base_url", defaults.get("base_url", "")),
        "model": get_config(f"llm.{provider}.model", defaults.get("model", "")),
        "max_tokens": get_config(f"llm.{provider}.max_tokens", 2048),
        "temperature": get_config(f"llm.{provider}.temperature", 0.7),
    }


async def chat_with_llm(
    message: str,
    system_prompt: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    调用 LLM API 进行对话。支持 deepseek / openai / siliconflow。

    Args:
        message (str): 用户消息。
        system_prompt (Optional[str]): 系统提示词。
        provider (Optional[str]): LLM 提供商。留空则读取 config.yaml 的 llm.default_provider。

    Returns:
        Dict[str, Any]: {"provider", "model", "reply", "usage"}
    """
    effective_provider = provider or get_config("llm.default_provider", "deepseek")
    logger.info(f"调用 LLM [{effective_provider}]，消息长度: {len(message)}")

    try:
        api_key = await asyncio.to_thread(_get_api_key_for_provider, effective_provider)
        cfg = _get_provider_config(effective_provider)
    except Exception as e:
        raise RuntimeError(f"读取 LLM 配置失败: {e}")

    if not cfg["base_url"] or not cfg["model"]:
        raise RuntimeError(f"provider '{effective_provider}' 的 base_url 或 model 未配置")

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=cfg["base_url"])

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        response = await client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            max_tokens=cfg["max_tokens"],
            temperature=cfg["temperature"],
        )

        reply = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        }
        logger.info(f"LLM [{effective_provider}] 回复成功，Token: {usage}")
        return {"provider": effective_provider, "model": cfg["model"], "reply": reply, "usage": usage}
    except Exception as e:
        raise RuntimeError(f"LLM [{effective_provider}] 调用失败: {e}")


# 展院兼容旧代码的内部帮气函数
def _get_api_key() -> str:
    """密封兼容：为 generate_metadata / summarize_content 提供 deepseek key。"""
    return _get_api_key_for_provider("deepseek")


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


SUMMARY_SYSTEM_PROMPT = """你是一个专业的文档总结助手。请根据用户提供的文档内容，生成一份结构化的 Markdown 摘要。

## 要求：
1. 摘要应包含：文档主题、核心要点（3-7 条）、关键结论
2. 使用 Markdown 格式，层次清晰
3. 语言简洁精炼，保留关键信息
4. 如果内容包含数据或案例，适当引用
5. 摘要长度控制在 100-500 字

## 输出格式：
# 📄 文档摘要：{文档标题}

## 主题概述
（一句话概括文档主题）

## 核心要点
- 要点 1
- 要点 2
- ...

## 关键结论
（总结性结论）
"""


async def summarize_content(content: str, title: str = "") -> str:
    """
    调用 DeepSeek 对文档内容生成结构化 Markdown 摘要。

    Args:
        content (str): 文档原文内容。
        title (str): 文档标题（用于提示 AI）。

    Returns:
        str: Markdown 格式的摘要文本。
    """
    # 截取前 6000 字，平衡摘要质量和 token 消耗
    preview = content[:6000]
    logger.info(f"AI 生成摘要，内容预览长度: {len(preview)}, 标题: {title}")

    try:
        api_key = await asyncio.to_thread(_get_api_key)
        base_url = get_config("llm.deepseek.base_url", "https://api.deepseek.com")
        model = get_config("llm.deepseek.model", "deepseek-chat")
    except Exception as e:
        logger.warning(f"读取 LLM 配置失败，跳过摘要生成: {e}")
        return ""

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        user_msg = f"请为以下文档生成摘要：\n\n"
        if title:
            user_msg += f"文档标题：{title}\n\n"
        user_msg += f"文档内容：\n{preview}"

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1024,
            temperature=0.5,
        )

        summary = response.choices[0].message.content.strip()
        usage = response.usage
        logger.info(
            f"AI 摘要生成成功，长度: {len(summary)}，"
            f"Token: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}"
        )
        return summary

    except Exception as e:
        logger.warning(f"AI 摘要生成失败，跳过: {e}")
        return ""