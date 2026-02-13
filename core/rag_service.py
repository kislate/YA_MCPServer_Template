"""
RAG (Retrieval-Augmented Generation) 服务模块

提供以下功能：
- ask_knowledge: 检索知识库 + 记忆库 + LLM 生成回答 + 关联推荐
"""

import asyncio
from typing import Dict, Any, Optional, List
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("rag_service")

RAG_SYSTEM_PROMPT = """你是一个专业的知识问答助手。基于以下检索到的知识内容回答问题。

## 规则：
1. 只基于提供的知识内容回答，不编造
2. 知识不足时明确告知用户
3. 标注信息来源
4. 条理清晰

## 检索到的知识：
{context}

{memory_context}
如果以上知识不包含答案，回答"根据现有知识库暂无相关信息，建议添加相关知识后再次提问。"
"""

DIRECT_ANSWER_PROMPT = """你是一个知识型助手。用户的问题在知识库中没有找到匹配内容。
请基于你自己的知识直接回答用户问题。

{profile_context}

## 规则：
1. 给出准确、有用的回答
2. 如果不确定，明确说明
3. 格式清晰，适当使用 Markdown
4. 在回答末尾说明此回答来自 AI 通用知识而非知识库"""


async def ask_knowledge(
    question: str,
    top_k: int = 5,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    基于知识库 + 记忆库的 RAG 智能问答。

    流程:
    1. 语义检索知识库（主要来源）
    2. 语义检索记忆库（补充来源）
    3. 合并上下文 → LLM 生成回答
    4. 异步后处理: 提取用户画像 + 生成补充知识存入记忆库

    Args:
        question (str): 用户问题。
        top_k (int): 检索片段数，默认 5。
        provider (Optional[str]): LLM 提供商。

    Returns:
        Dict[str, Any]: 回答 + 引用来源 + 关联推荐。
    """
    logger.info(f"RAG 问答: '{question[:50]}'")

    # ── 1. 并行检索知识库 + 记忆库 ──
    try:
        from core.knowledge_store import search_knowledge
        from core.memory_store import search_memory, get_user_profile
    except ImportError as e:
        raise RuntimeError(f"无法导入模块: {e}")

    try:
        kb_task = search_knowledge(query=question, top_k=top_k)
        mem_task = search_memory(query=question, top_k=3)
        profile_task = get_user_profile()

        search_results, memory_results, user_profile = await asyncio.gather(
            kb_task, mem_task, profile_task
        )
    except Exception as e:
        raise RuntimeError(f"检索失败: {e}")

    results = search_results.get("results", [])  # 已在 search_knowledge 中过滤低相关度

    # ── 2. 构建记忆库上下文 ──
    memory_sources = []
    if memory_results:
        for m in memory_results:
            memory_sources.append({
                "title": m.get("title", ""),
                "relevance": m.get("relevance", 0),
                "confidence": m.get("confidence", 0),
                "source": "memory",
            })

    has_kb = len(results) > 0
    has_mem = len(memory_results) > 0

    # ── 3. 分支逻辑 ──
    try:
        from core.llm_service import chat_with_llm
    except ImportError as e:
        raise RuntimeError(f"无法导入 LLM 模块: {e}")

    if has_kb or has_mem:
        # ═══ 有相关知识 → RAG 模式 ═══
        context_parts, sources = [], []
        for i, r in enumerate(results):
            raw_info = f", 原始文件: {r['raw_file']}" if r.get('raw_file') else ""
            context_parts.append(
                f"【知识{i+1}】(来源: {r.get('title', '未知')}, 相关度: {r.get('relevance', 0):.2f}{raw_info})\n{r['content']}"
            )
            sources.append({
                "title": r.get("title", "未知"),
                "relevance": r.get("relevance", 0),
                "raw_file": r.get("raw_file", ""),
            })

        # 记忆库上下文
        memory_context = ""
        if has_mem:
            mem_parts = []
            for i, m in enumerate(memory_results):
                mem_parts.append(
                    f"【记忆{i+1}】(标题: {m.get('title', '未知')}, 置信度: {m.get('confidence', 0):.1f})\n{m['content']}"
                )
            memory_context = "## 记忆库中的相关补充：\n" + "\n\n---\n\n".join(mem_parts)

        system_prompt = RAG_SYSTEM_PROMPT.format(
            context="\n\n---\n\n".join(context_parts) if context_parts else "（无匹配知识）",
            memory_context=memory_context,
        )

        try:
            llm_resp = await chat_with_llm(message=question, system_prompt=system_prompt, provider=provider)
        except Exception as e:
            raise RuntimeError(f"LLM 生成失败: {e}")

        answer = llm_resp["reply"]
        mode = "rag"
        logger.info(f"RAG 模式完成，知识库 {len(results)} 片段 + 记忆库 {len(memory_results)} 条")

    else:
        # ═══ 无匹配知识 → AI 直接回答模式 ═══
        logger.info("知识库和记忆库均无匹配，切换为 AI 直接回答模式")
        sources = []

        # 利用用户画像个性化回答
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
                profile_context = f"用户画像：{'; '.join(parts)}。请据此调整回答的深度和风格。"

        system_prompt = DIRECT_ANSWER_PROMPT.format(profile_context=profile_context)

        try:
            llm_resp = await chat_with_llm(message=question, system_prompt=system_prompt, provider=provider)
        except Exception as e:
            raise RuntimeError(f"LLM 生成失败: {e}")

        answer = llm_resp["reply"]
        mode = "ai_direct"
        logger.info("AI 直接回答完成")

    # ── 4. 异步后处理（不阻塞返回） ──
    asyncio.create_task(
        _post_process(question, answer, sources, user_profile)
    )

    return {
        "question": question,
        "answer": answer,
        "mode": mode,  # "rag" 或 "ai_direct"
        "sources": sources,
        "memory_sources": memory_sources,
        "llm_provider": llm_resp["provider"],
        "context_chunks_used": len(results) + len(memory_results),
        "token_usage": llm_resp["usage"],
    }


async def _post_process(
    question: str,
    answer: str,
    sources: List[Dict],
    user_profile: Dict[str, Any],
):
    """
    RAG 问答后的异步处理：
    1. 提取用户画像特征
    2. 生成补充知识存入记忆库
    """
    try:
        from core.llm_service import extract_user_profile, generate_supplementary_knowledge
        from core.memory_store import update_user_profile, add_memory

        # ① 提取用户画像（低成本，每次都做）
        profile_update = await extract_user_profile(question, answer)
        if profile_update:
            await update_user_profile(profile_update)

        # ② 生成补充知识（写入记忆库）
        existing_titles = [s.get("title", "") for s in sources if s.get("title")]
        supplements = await generate_supplementary_knowledge(
            question=question,
            answer=answer,
            existing_sources=existing_titles,
            user_profile=user_profile,
        )

        for item in supplements:
            if item.get("content"):
                await add_memory(
                    content=item["content"],
                    title=item.get("title", ""),
                    tags=item.get("tags", ""),
                    source_question=question,
                    confidence=0.7,
                )

        logger.info(f"后处理完成: 画像更新={bool(profile_update)}, 补充知识={len(supplements)}条")

    except Exception as e:
        logger.warning(f"后处理失败（不影响回答）: {e}")
