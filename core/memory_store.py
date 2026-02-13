"""
记忆库模块 - 用户画像 + AI 补充知识

两层存储：
1. 用户画像 (user_profile.json): 从对话中提取的用户特征
2. AI 补充知识 (ChromaDB user_memory collection): AI 生成的相关知识片段

特性：
- 自动积累用户偏好和学习领域
- 自动生成补充知识，语义可检索
- 超过容量上限时智能淘汰（LRU + hit_count + confidence 综合评分）
- 高频命中的记忆可晋升为永久知识
"""

import asyncio
import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("memory_store")

MEMORY_DIR = Path("./data/memory")
PROFILE_PATH = MEMORY_DIR / "user_profile.json"

_memory_collection = None
_memory_lock = threading.Lock()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  用户画像（JSON 文件）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _load_profile() -> Dict[str, Any]:
    """加载用户画像，不存在则返回空结构。"""
    if PROFILE_PATH.exists():
        try:
            return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"用户画像加载失败: {e}")
    return {
        "interests": [],      # 兴趣领域 ["Python", "机器学习"]
        "level": "",           # 学习阶段 "初学者" / "进阶" / "高级"
        "preferences": [],     # 偏好 ["喜欢代码示例", "中文回答"]
        "frequent_topics": {}, # 话题频率 {"装饰器": 3, "列表": 1}
        "updated_at": "",
    }


def _save_profile(profile: Dict[str, Any]):
    """保存用户画像。"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    profile["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.debug("用户画像已保存")


async def update_user_profile(profile_update: Dict[str, Any]):
    """
    合并 AI 提取的用户特征到画像。

    Args:
        profile_update: AI 提取的特征，格式:
            {"interests": ["Python"], "level": "初学者",
             "preferences": ["喜欢代码示例"], "topics": ["装饰器"]}
    """
    def _sync_update():
        profile = _load_profile()

        # 合并 interests（去重）
        new_interests = profile_update.get("interests", [])
        if new_interests:
            existing = set(profile["interests"])
            for item in new_interests:
                if item and item not in existing:
                    profile["interests"].append(item)
            # 最多保留 20 个
            profile["interests"] = profile["interests"][-20:]

        # 更新 level（取最新）
        new_level = profile_update.get("level", "")
        if new_level:
            profile["level"] = new_level

        # 合并 preferences（去重）
        new_prefs = profile_update.get("preferences", [])
        if new_prefs:
            existing = set(profile["preferences"])
            for item in new_prefs:
                if item and item not in existing:
                    profile["preferences"].append(item)
            profile["preferences"] = profile["preferences"][-10:]

        # 累加话题频率
        new_topics = profile_update.get("topics", [])
        for topic in new_topics:
            if topic:
                profile["frequent_topics"][topic] = (
                    profile["frequent_topics"].get(topic, 0) + 1
                )

        _save_profile(profile)
        logger.info(f"用户画像已更新: interests={len(profile['interests'])}, topics={len(profile['frequent_topics'])}")

    await asyncio.to_thread(_sync_update)


async def get_user_profile() -> Dict[str, Any]:
    """获取用户画像。"""
    return await asyncio.to_thread(_load_profile)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI 补充知识（ChromaDB collection）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _get_memory_collection():
    """获取记忆库集合（单例，复用 knowledge_store 的 client 和 embedding）。"""
    global _memory_collection
    if _memory_collection is not None:
        return _memory_collection
    with _memory_lock:
        if _memory_collection is not None:
            return _memory_collection
        from core.knowledge_store import _get_client, _get_embedding_function
        collection_name = get_config("memory.collection_name", "user_memory")
        _memory_collection = _get_client().get_or_create_collection(
            name=collection_name,
            embedding_function=_get_embedding_function(),
        )
        logger.info(f"记忆库集合 '{collection_name}' 已加载，当前 {_memory_collection.count()} 条")
    return _memory_collection


async def add_memory(
    content: str,
    title: str = "",
    tags: str = "",
    source_question: str = "",
    confidence: float = 0.7,
) -> Dict[str, Any]:
    """
    添加一条 AI 补充知识到记忆库。

    Args:
        content: 补充知识内容。
        title: 标题。
        tags: 标签（逗号分隔）。
        source_question: 触发生成此知识的原始问题。
        confidence: AI 对此知识的置信度 (0~1)。

    Returns:
        添加结果。
    """
    def _sync_add():
        collection = _get_memory_collection()
        max_items = get_config("memory.max_items", 50)

        # 淘汰：超出上限时删除评分最低的
        current_count = collection.count()
        if current_count >= max_items:
            _evict_lowest(collection, count=current_count - max_items + 1)

        mem_id = f"mem_{int(time.time())}_{hash(content) % 10000:04d}"
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        collection.add(
            ids=[mem_id],
            documents=[content],
            metadatas=[{
                "title": title,
                "tags": tags,
                "source_question": source_question,
                "confidence": confidence,
                "hit_count": 0,
                "created_at": now,
                "last_accessed": now,
            }],
        )
        logger.info(f"记忆添加: {mem_id}, title='{title}', confidence={confidence}")
        return {"id": mem_id, "title": title, "message": "记忆已添加"}

    try:
        return await asyncio.to_thread(_sync_add)
    except Exception as e:
        raise RuntimeError(f"添加记忆失败: {e}")


def _evict_lowest(collection, count: int = 1):
    """淘汰评分最低的 count 条记忆。"""
    all_data = collection.get()
    if not all_data["ids"]:
        return

    now_ts = time.time()
    scored = []
    for i, mid in enumerate(all_data["ids"]):
        meta = all_data["metadatas"][i]
        hit = meta.get("hit_count", 0)
        conf = meta.get("confidence", 0.5)

        # 计算 recency: 距上次访问的天数，越近分越高
        try:
            la = time.mktime(time.strptime(meta.get("last_accessed", ""), "%Y-%m-%d %H:%M:%S"))
            days_ago = (now_ts - la) / 86400
        except Exception:
            days_ago = 30  # 解析失败当作很久没用

        recency = max(0, 1.0 - days_ago / 30)  # 30天内线性衰减到0
        score = hit * 0.4 + conf * 0.3 + recency * 0.3
        scored.append((mid, score))

    scored.sort(key=lambda x: x[1])
    to_delete = [s[0] for s in scored[:count]]
    if to_delete:
        collection.delete(ids=to_delete)
        logger.info(f"淘汰 {len(to_delete)} 条低分记忆: {to_delete}")


async def search_memory(
    query: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    语义搜索记忆库。

    Args:
        query: 搜索查询。
        top_k: 返回条数。

    Returns:
        匹配的记忆列表。
    """
    def _sync_search():
        collection = _get_memory_collection()
        if collection.count() == 0:
            return []

        n = min(top_k, collection.count())
        results = collection.query(query_texts=[query], n_results=n)

        items = []
        if results and results["ids"] and results["ids"][0]:
            ids_to_update = []
            for i in range(len(results["ids"][0])):
                dist = results["distances"][0][i] if results.get("distances") else 0
                relevance = round(1 - dist, 4)
                meta = results["metadatas"][0][i]

                # 过滤低相关度
                min_rel = get_config("memory.min_relevance", 0.2)
                if relevance < min_rel:
                    continue

                items.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "title": meta.get("title", ""),
                    "tags": meta.get("tags", ""),
                    "relevance": relevance,
                    "confidence": meta.get("confidence", 0),
                    "hit_count": meta.get("hit_count", 0),
                    "source": "memory",
                })
                ids_to_update.append((results["ids"][0][i], meta))

            # 更新 hit_count 和 last_accessed
            for mid, meta in ids_to_update:
                try:
                    collection.update(
                        ids=[mid],
                        metadatas=[{
                            **meta,
                            "hit_count": meta.get("hit_count", 0) + 1,
                            "last_accessed": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }],
                    )
                except Exception:
                    pass  # 更新失败不影响搜索结果

        logger.debug(f"记忆搜索 '{query[:30]}' → {len(items)} 条")
        return items

    try:
        return await asyncio.to_thread(_sync_search)
    except Exception as e:
        logger.warning(f"记忆搜索失败: {e}")
        return []


async def list_memories(limit: int = 20) -> Dict[str, Any]:
    """列出记忆库所有条目。"""
    def _sync_list():
        collection = _get_memory_collection()
        all_data = collection.get(limit=limit)

        items = []
        for i in range(len(all_data["ids"])):
            meta = all_data["metadatas"][i]
            preview = all_data["documents"][i]
            items.append({
                "id": all_data["ids"][i],
                "title": meta.get("title", ""),
                "tags": meta.get("tags", ""),
                "confidence": meta.get("confidence", 0),
                "hit_count": meta.get("hit_count", 0),
                "created_at": meta.get("created_at", ""),
                "last_accessed": meta.get("last_accessed", ""),
                "preview": preview[:100] + "..." if len(preview) > 100 else preview,
            })

        return {
            "total": collection.count(),
            "items": items,
        }

    try:
        return await asyncio.to_thread(_sync_list)
    except Exception as e:
        raise RuntimeError(f"列出记忆失败: {e}")


async def clear_memories() -> Dict[str, str]:
    """清空记忆库。"""
    def _sync_clear():
        global _memory_collection
        from core.knowledge_store import _get_client, _get_embedding_function
        client = _get_client()
        name = get_config("memory.collection_name", "user_memory")
        try:
            client.delete_collection(name)
        except Exception:
            pass
        _memory_collection = client.get_or_create_collection(
            name=name,
            embedding_function=_get_embedding_function(),
        )
        return {"message": "记忆库已清空"}

    try:
        return await asyncio.to_thread(_sync_clear)
    except Exception as e:
        raise RuntimeError(f"清空记忆失败: {e}")


async def get_memory_stats() -> Dict[str, Any]:
    """获取记忆库统计。"""
    def _sync_stats():
        collection = _get_memory_collection()
        total = collection.count()
        profile = _load_profile()

        # 统计记忆的标签分布
        tag_counts = {}
        if total > 0:
            all_data = collection.get()
            for meta in all_data["metadatas"]:
                for t in meta.get("tags", "").split(","):
                    t = t.strip()
                    if t:
                        tag_counts[t] = tag_counts.get(t, 0) + 1

        max_items = get_config("memory.max_items", 50)
        return {
            "total_memories": total,
            "max_capacity": max_items,
            "usage_percent": round(total / max_items * 100, 1) if max_items > 0 else 0,
            "tag_distribution": tag_counts,
            "user_profile": {
                "interests": profile.get("interests", []),
                "level": profile.get("level", ""),
                "top_topics": dict(
                    sorted(
                        profile.get("frequent_topics", {}).items(),
                        key=lambda x: x[1],
                        reverse=True,
                    )[:10]
                ),
            },
        }

    try:
        return await asyncio.to_thread(_sync_stats)
    except Exception as e:
        raise RuntimeError(f"记忆统计失败: {e}")


def warm_up_memory():
    """预热记忆库集合。"""
    try:
        _ = _get_memory_collection()
        logger.info("记忆库预热完成")
    except Exception as e:
        logger.warning(f"记忆库预热失败: {e}")
