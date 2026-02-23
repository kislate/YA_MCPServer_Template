"""
RAG (Retrieval-Augmented Generation) 服务模块

提供以下功能：
- ask_knowledge: 检索知识库 + LLM 生成回答
  - 高相关 / 低相关 分级处理
  - 高相关结果不足时自动 Web 搜索补充
  - 无论是否有检索结果，始终调用 LLM 生成答案（结合用户画像/通用知识）
  - 引用信息包含原文片段
"""

from typing import Dict, Any, Optional
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("rag_service")

# 有检索上下文时使用
_PROMPT_WITH_KNOWLEDGE = """你是一个知识渊博、循循善诱的学习伙伴。你的风格是：
- 引经据典：回答时自然地引用检索到的材料，用「根据《标题》中的记录…」「《标题》里提到…」这样的方式
  把来源融入叙述，让答案有出处、有依据，而不是把材料和回答分开
- 不照本宣科：用自己的语言转述和解释，加入类比、举例，帮用户真正理解，而不是直接粘贴原文
- 善于挖掘线索：哪怕某条材料被标注「低相关」，也要凭语义判断它是否真的有用，有时边缘材料里藏着关键线索
- 自然补充：材料不够时，结合自身知识补充，像朋友聊天一样带出来，不必刻意区分
- 适时引导：答完主线后，可以提一两个值得延伸思考的问题
- 语气温和，用 Markdown 让答案清晰易读

{profile_context}
{quality_hint}
---
以下是检索到的参考材料（来自知识库或网络），已按相关度排序。
「高相关」/「低相关」只是向量距离的机械判断，请结合语义判断每条材料的真实价值：

{context}
---
"""  # noqa: E501

# 无任何检索上下文时使用：纯 AI 模式
_PROMPT_NO_CONTEXT = """你是一个知识渊博、循循善诱的学习伙伴。
知识库里暂时还没有与该问题相关的内容，请在回答开头自然地提一下这一点（一句话即可，不必强调），
然后凭自己的知识来回答。

{profile_context}

回答时请引经据典，循序渐进，多用例子和类比，在结尾可以建议用户把相关资料添加到知识库。
语气温和，用 Markdown 让答案清晰易读。
"""  # noqa: E501


async def ask_knowledge(
    question: str,
    top_k: int = 5,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    基于知识库的 RAG 智能问答。

    流程:
      1. 语义检索 → 按相关度分为「高相关」和「低相关」
      2. 高相关不足 → 触发 Web fallback 补充
      3. 无论上下文是否为空，始终调用 LLM 生成答案
         - 有上下文: 用 _PROMPT_WITH_KNOWLEDGE（允许 AI 补充自身知识）
         - 无上下文: 用 _PROMPT_NO_CONTEXT（纯 AI 模式）

    Args:
        question: 用户问题。
        top_k: 检索片段数，默认 5。
        provider: LLM 提供商，留空使用 config 默认值。

    Returns:
        Dict 包含 answer / sources / high_quality_chunks / web_fallback_used /
        ai_knowledge_used / llm_provider / token_usage。
    """
    logger.info(f"RAG 问答: '{question[:50]}'")

    from core.knowledge_store import search_knowledge

    # ── 1. 检索 ──────────────────────────────────────────────────────────────
    search_results = await search_knowledge(query=question, top_k=top_k)
    results = search_results.get("results", [])

    high_threshold = get_config("rag.ai_answer.high_relevance_threshold", 0.6)

    # 高相关：用于 web fallback 触发判断
    high_quality = [r for r in results if r.get("relevance", 0) >= high_threshold]
    # 低相关：所有不足高阈值的结果都传给 LLM，让模型自行判断有用性
    low_quality = [r for r in results if r.get("relevance", 0) < high_threshold]

    # ── 2. Web fallback（高相关不足时触发）──────────────────────────────────
    web_results_used = []
    web_fallback_enabled = get_config("rag.web_fallback.enabled", True)
    min_local = get_config("rag.web_fallback.min_local_results", 1)

    if web_fallback_enabled and len(high_quality) < min_local:
        logger.info(
            f"高相关结果仅 {len(high_quality)} 条（阈值 {high_threshold}），触发 Web fallback"
        )
        try:
            from core.web_search_service import search_and_summarize
            web_count = get_config("rag.web_fallback.web_results", 3)
            web_resp = await search_and_summarize(
                query=question, max_results=web_count, fetch_content=True
            )
            for item in web_resp.get("results", []):
                snippet = item.get("content", item.get("snippet", ""))[:600]
                if snippet:
                    web_results_used.append({
                        "title": item.get("title", "网络搜索"),
                        "relevance": 0.0,
                        "source": item.get("url", ""),
                        "snippet": snippet,
                        "from_web": True,
                    })
            logger.info(f"Web fallback 补充 {len(web_results_used)} 条结果")
        except Exception as e:
            logger.warning(f"Web fallback 失败: {e}")

    # ── 3. 构建上下文 ─────────────────────────────────────────────────────────
    context_parts: list[str] = []
    sources: list[dict] = []

    # 高相关本地知识
    for i, r in enumerate(high_quality):
        snippet = r["content"][:300].strip()
        raw_info = f", 文件: {r['raw_file']}" if r.get("raw_file") else ""
        context_parts.append(
            f"【知识库-高相关{i+1}】(来源: {r.get('title','未知')}, 相关度: {r.get('relevance',0):.2f}{raw_info})\n{r['content']}"
        )
        sources.append({
            "title": r.get("title", "未知"),
            "relevance": r.get("relevance", 0),
            "quality": "high",
            "raw_file": r.get("raw_file", ""),
            "base_id": r.get("base_id", ""),
            "snippet": snippet,
            "from_web": False,
        })

    # 低相关本地知识（辅助参考）
    for i, r in enumerate(low_quality):
        snippet = r["content"][:200].strip()
        raw_info = f", 文件: {r['raw_file']}" if r.get("raw_file") else ""
        context_parts.append(
            f"【知识库-低相关{i+1}】(来源: {r.get('title','未知')}, 相关度: {r.get('relevance',0):.2f}{raw_info})\n{r['content']}"
        )
        sources.append({
            "title": r.get("title", "未知"),
            "relevance": r.get("relevance", 0),
            "quality": "low",
            "raw_file": r.get("raw_file", ""),
            "base_id": r.get("base_id", ""),
            "snippet": snippet,
            "from_web": False,
        })

    # Web 补充内容
    for j, w in enumerate(web_results_used):
        context_parts.append(
            f"【网络{j+1}】(来源: {w['title']}, URL: {w['source']})\n{w['snippet']}"
        )
        sources.append({
            "title": w["title"],
            "relevance": w["relevance"],
            "quality": "web",
            "raw_file": "",
            "base_id": "",
            "snippet": w["snippet"],
            "source_url": w["source"],
            "from_web": True,
        })

    # ── 4. 用户画像 ───────────────────────────────────────────────────────────
    profile_ctx = ""
    try:
        from core.user_profile_service import get_profile_context
        profile_ctx = get_profile_context()
    except Exception:
        pass

    # ── 5. 选择 Prompt 模板，始终调用 LLM ─────────────────────────────────────
    has_context = bool(context_parts)
    ai_answer_enabled = get_config("rag.ai_answer.enabled", True)
    allow_llm_knowledge = get_config("rag.ai_answer.allow_llm_knowledge", True)

    if has_context:
        # 没有高相关结果时给 LLM 一个委婉提示，让它在回答开头说明
        if not high_quality and not web_results_used:
            quality_hint = (
                "> **提示（仅供你参考，不要原封不动输出此行）**："
                "知识库中暂未找到与该问题高度吻合的内容，以下材料相关度较低。"
                "请在回答开头用一两句话委婉地告知用户，然后再基于材料和自身知识尽力回答。\n"
            )
        elif not high_quality:
            quality_hint = (
                "> **提示（仅供你参考，不要原封不动输出此行）**："
                "本地知识库暂无高相关内容，以下包含网络补充结果，请合理引用。\n"
            )
        else:
            quality_hint = ""
        system_prompt = _PROMPT_WITH_KNOWLEDGE.format(
            context="\n\n---\n\n".join(context_parts),
            profile_context=profile_ctx,
            quality_hint=quality_hint,
        )
    else:
        if not ai_answer_enabled:
            logger.info("无检索上下文且 ai_answer 已禁用，返回空答案提示")
            return {
                "question": question,
                "answer": "知识库中暂无相关内容，请先用 add_knowledge 添加知识，或开启 rag.ai_answer.enabled。",
                "sources": [],
                "high_quality_chunks": 0,
                "context_chunks_used": 0,
                "web_fallback_used": False,
                "ai_knowledge_used": False,
            }
        system_prompt = _PROMPT_NO_CONTEXT.format(profile_context=profile_ctx)

    from core.llm_service import chat_with_llm
    llm_resp = await chat_with_llm(
        message=question, system_prompt=system_prompt, provider=provider
    )

    ai_knowledge_used = (not has_context) or (
        allow_llm_knowledge and len(high_quality) < min_local
    )

    logger.info(
        f"RAG 完成 | 高相关 {len(high_quality)} | 低相关 {len(low_quality)} | "
        f"Web {len(web_results_used)} | AI补充 {ai_knowledge_used}"
    )

    return {
        "question": question,
        "answer": llm_resp["reply"],
        "sources": sources,
        "llm_provider": llm_resp["provider"],
        "high_quality_chunks": len(high_quality),
        "context_chunks_used": len(high_quality) + len(low_quality),
        "web_fallback_used": len(web_results_used) > 0,
        "ai_knowledge_used": ai_knowledge_used,
        "token_usage": llm_resp["usage"],
    }
