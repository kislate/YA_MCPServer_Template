"""
知识存储模块 - ChromaDB 向量数据库封装

提供以下功能：
- add_knowledge: 添加知识到向量数据库
- search_knowledge: 语义搜索知识
- list_knowledge: 列出知识条目
- delete_knowledge: 删除知识
- get_stats: 获取统计信息

Embedding 使用硅基流动 (SiliconFlow) 的 OpenAI 兼容接口，
模型 BAAI/bge-m3，无需下载本地模型文件。
"""

import asyncio
import json
import os
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("knowledge_store")

_client: Optional[chromadb.PersistentClient] = None
_collection = None
_embedding_fn = None
_cached_sf_key: Optional[str] = None
_init_lock = threading.Lock()

RAW_DIR = Path("./data/raw")
ATTACHMENT_DIR = Path("./data/attachments")


def _get_embedding_api_key() -> str:
    """从 SOPS 获取 SiliconFlow API Key，环境变量作为备用。结果缓存。"""
    global _cached_sf_key
    if _cached_sf_key:
        return _cached_sf_key

    # 优先从 SOPS 获取
    try:
        from modules.YA_Secrets.secrets_parser import get_secret
        key = get_secret("siliconflow_api_key")
        if key:
            logger.debug("从 SOPS 获取 SiliconFlow API Key 成功")
            _cached_sf_key = key
            return key
    except Exception as e:
        logger.warning(f"SOPS 获取 Embedding API Key 失败: {e}")

    # 备用：环境变量
    key = os.environ.get("SILICONFLOW_API_KEY")
    if key:
        logger.debug("从环境变量获取 SiliconFlow API Key")
        return key

    raise RuntimeError(
        "未找到 SiliconFlow API Key，请通过 SOPS 加密到 env.yaml（key: siliconflow_api_key）"
        "或设置环境变量 SILICONFLOW_API_KEY"
    )


def _get_embedding_function() -> OpenAIEmbeddingFunction:
    """获取 Embedding 函数（单例，线程安全），使用硅基流动 OpenAI 兼容接口。"""
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn
    with _init_lock:
        if _embedding_fn is not None:
            return _embedding_fn
        api_key = _get_embedding_api_key()
        api_base = get_config(
            "knowledge.embedding.base_url",
            "https://api.siliconflow.cn/v1"
        )
        model = get_config(
            "knowledge.embedding.model",
            "BAAI/bge-m3"
        )
        _embedding_fn = OpenAIEmbeddingFunction(
            api_key=api_key,
            api_base=api_base,
            model_name=model,
        )
        logger.info(f"Embedding 初始化: model={model}, base={api_base}")
    return _embedding_fn


def _get_client() -> chromadb.PersistentClient:
    """获取 ChromaDB 客户端（单例，线程安全）"""
    global _client
    if _client is not None:
        return _client
    with _init_lock:
        if _client is not None:
            return _client
        path = get_config("knowledge.chromadb.persist_directory", "./data/chromadb")
        logger.info(f"初始化 ChromaDB: {path}")
        _client = chromadb.PersistentClient(path=path)
    return _client


def get_collection():
    """获取知识库集合（使用 SiliconFlow embedding，线程安全）"""
    global _collection
    if _collection is not None:
        return _collection
    with _init_lock:
        if _collection is not None:
            return _collection
        name = get_config("knowledge.chromadb.collection_name", "knowledge_base")
        ef = _get_embedding_function()
        _collection = _get_client().get_or_create_collection(
            name=name,
            embedding_function=ef,
        )
        logger.info(f"集合 '{name}' 已加载，当前 {_collection.count()} 条")
    return _collection


def _save_raw_markdown(
    base_id: str, content: str, title: str, tags: list, source: str
) -> str:
    """保存原始 Markdown 到 data/raw/{base_id}.md，返回相对路径。"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RAW_DIR / f"{base_id}.md"

    # 写入 YAML frontmatter + 原始内容
    frontmatter = f"""---
id: {base_id}
title: {title}
tags: [{', '.join(tags)}]
source: {source}
---

"""
    filepath.write_text(frontmatter + content, encoding="utf-8")
    logger.info(f"原始 Markdown 已保存: {filepath}")
    return str(filepath)


def _delete_raw_markdown(base_id: str) -> bool:
    """删除原始 Markdown 文件，返回是否成功。"""
    filepath = RAW_DIR / f"{base_id}.md"
    if filepath.exists():
        filepath.unlink()
        logger.info(f"原始 Markdown 已删除: {filepath}")
        return True
    return False

def _delete_all_files(base_id: str) -> None:
    """删除知识相关的所有文件（Markdown + 附件）。"""
    _delete_raw_markdown(base_id)
    _delete_attachment(base_id)


def _get_raw_file_path(base_id: str) -> str:
    """获取原始 Markdown 文件路径（如果存在）。"""
    filepath = RAW_DIR / f"{base_id}.md"
    return str(filepath) if filepath.exists() else ""


def _save_attachment(
    base_id: str, source_path: str, doc_type: str = "pdf"
) -> str:
    """
    保存原始文件到 data/attachments/{base_id}.{ext}
    
    Args:
        base_id: 知识 ID
        source_path: 原始文件路径
        doc_type: 文档类型（pdf, html 等）
        
    Returns:
        str: 附件保存路径
    """
    import shutil
    
    ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)
    source = Path(source_path)
    
    if not source.exists():
        logger.warning(f"源文件不存在: {source_path}")
        return ""
    
    # 保留原始扩展名或使用 doc_type
    ext = source.suffix if source.suffix else f".{doc_type}"
    dest_path = ATTACHMENT_DIR / f"{base_id}{ext}"
    
    try:
        shutil.copy2(source_path, dest_path)
        logger.info(f"附件已保存: {dest_path}")
        return str(dest_path)
    except Exception as e:
        logger.error(f"保存附件失败: {e}")
        return ""


def _delete_attachment(base_id: str) -> bool:
    """删除附件文件（支持多种扩展名）。"""
    deleted = False
    for ext in [".pdf", ".html", ".docx", ".pptx"]:
        filepath = ATTACHMENT_DIR / f"{base_id}{ext}"
        if filepath.exists():
            filepath.unlink()
            logger.info(f"附件已删除: {filepath}")
            deleted = True
    return deleted


def _get_attachment_path(base_id: str) -> str:
    """获取附件路径（如果存在）。"""
    for ext in [".pdf", ".html", ".docx", ".pptx"]:
        filepath = ATTACHMENT_DIR / f"{base_id}{ext}"
        if filepath.exists():
            return str(filepath)
    return ""


async def add_knowledge(
    content: str,
    title: str = "",
    tags: str = "",
    source: str = "",
) -> Dict[str, Any]:
    """
    添加知识到向量数据库（自动分块 + 自动向量化）。
    原始内容同时保存为 Markdown 文件到 data/raw/{id}.md。
    如果 title/tags/source 缺失，自动调用 AI 生成。

    Args:
        content (str): 知识内容文本。
        title (str): 标题（留空则 AI 自动生成）。
        tags (str): 标签（留空则 AI 自动生成，逗号分隔）。
        source (str): 来源（留空则 AI 自动生成）。

    Returns:
        Dict[str, Any]: 添加结果，包含 ID、分块数和原始文件路径。
    """
    logger.info(f"添加知识: title='{title}', len={len(content)}")

    # 如果 title/tags/source 有缺失，调用 AI 自动生成
    if not title or not tags or not source:
        try:
            from core.llm_service import generate_metadata
            ai_meta = await generate_metadata(content)
            if not title:
                title = ai_meta.get("title", "未命名")
                logger.info(f"AI 生成标题: {title}")
            if not tags:
                tags = ai_meta.get("tags", "")
                logger.info(f"AI 生成标签: {tags}")
            if not source:
                source = ai_meta.get("source", "用户笔记")
                logger.info(f"AI 生成来源: {source}")
        except Exception as e:
            logger.warning(f"AI 生成元数据失败，使用默认值: {e}")
            title = title or "未命名"
            tags = tags or ""
            source = source or "用户笔记"

    try:
        from core.document_processor import split_text
    except ImportError as e:
        raise RuntimeError(f"无法导入文档处理模块: {e}")

    def _sync_add():
        """同步执行，放到线程池避免阻塞事件循环。"""
        collection = get_collection()
        chunk_size = get_config("knowledge.chunking.chunk_size", 500)
        chunk_overlap = get_config("knowledge.chunking.chunk_overlap", 100)
        chunks = split_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        base_id = f"kb_{uuid.uuid4().hex[:8]}"
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        # 保存原始 Markdown 文件
        raw_file = _save_raw_markdown(base_id, content, title, tag_list, source)

        ids, documents, metadatas = [], [], []
        for i, chunk in enumerate(chunks):
            ids.append(f"{base_id}_chunk{i}")
            documents.append(chunk)
            metadatas.append({
                "title": title,
                "tags": ",".join(tag_list),
                "source": source,
                "base_id": base_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "raw_file": raw_file,
            })

        # 分批添加，每批最多 10 个块，避免 embedding API 超时
        BATCH_SIZE = 10
        for batch_start in range(0, len(ids), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(ids))
            logger.info(f"正在嵌入第 {batch_start+1}-{batch_end}/{len(ids)} 个片段...")
            collection.add(
                ids=ids[batch_start:batch_end],
                documents=documents[batch_start:batch_end],
                metadatas=metadatas[batch_start:batch_end],
            )

        logger.info(f"添加成功: {base_id}, {len(chunks)} 个片段, 原始文件: {raw_file}")
        return {
            "id": base_id,
            "title": title,
            "tags": tag_list,
            "chunks_count": len(chunks),
            "raw_file": raw_file,
            "message": "知识添加成功",
        }

    try:
        return await asyncio.to_thread(_sync_add)
    except Exception as e:
        raise RuntimeError(f"添加知识失败: {e}")


async def search_knowledge(
    query: str,
    top_k: int = 5,
    tag_filter: str = "",
) -> Dict[str, Any]:
    """
    语义搜索知识库。

    Args:
        query (str): 搜索查询。
        top_k (int): 返回前 K 条结果。
        tag_filter (str): 可选标签过滤。

    Returns:
        Dict[str, Any]: 搜索结果。

    Example:
        {"query": "装饰器", "total_results": 2, "results": [{"content": "...", "relevance": 0.85}]}
    """
    logger.info(f"搜索: '{query}', top_k={top_k}")

    def _sync_search():
        """同步执行，放到线程池避免阻塞事件循环。"""
        collection = get_collection()
        n = min(top_k, get_config("knowledge.retrieval.top_k", 5), max(collection.count(), 1))

        if collection.count() == 0:
            return {"query": query, "total_results": 0, "results": [], "message": "知识库为空"}

        query_params = {"query_texts": [query], "n_results": n}
        if tag_filter:
            query_params["where"] = {"tags": {"$contains": tag_filter}}

        results = collection.query(**query_params)

        formatted = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                dist = results["distances"][0][i] if results.get("distances") else 0
                meta = results["metadatas"][0][i]
                bid = meta.get("base_id", "")
                formatted.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "title": meta.get("title", ""),
                    "tags": meta.get("tags", ""),
                    "source": meta.get("source", ""),
                    "relevance": round(1 - dist, 4),
                    "base_id": bid,
                    "raw_file": meta.get("raw_file", "") or _get_raw_file_path(bid),
                })

        logger.info(f"搜索返回 {len(formatted)} 条")
        return {"query": query, "total_results": len(formatted), "results": formatted}

    try:
        return await asyncio.to_thread(_sync_search)
    except Exception as e:
        raise RuntimeError(f"搜索失败: {e}")


async def list_knowledge(tag_filter: str = "", limit: int = 100) -> Dict[str, Any]:
    """
    列出知识条目。

    Args:
        tag_filter (str): 标签过滤。
        limit (int): 最大返回数（默认 100，足够显示所有条目）。

    Returns:
        Dict[str, Any]: 知识列表。
    """
    def _sync_list():
        """同步执行，放到线程池避免阻塞事件循环。"""
        collection = get_collection()
        total_count = collection.count()
        # 获取所有分块以便去重，但限制最大数量
        get_params = {"limit": min(limit * 10, total_count) if total_count > 0 else limit}
        if tag_filter:
            get_params["where"] = {"tags": {"$contains": tag_filter}}

        results = collection.get(**get_params)

        seen = {}
        for i in range(len(results["ids"])):
            meta = results["metadatas"][i]
            bid = meta.get("base_id", results["ids"][i])
            if bid not in seen and len(seen) < limit:
                preview = results["documents"][i]
                seen[bid] = {
                    "id": bid,
                    "title": meta.get("title", "未命名"),
                    "tags": meta.get("tags", ""),
                    "source": meta.get("source", ""),
                    "total_chunks": meta.get("total_chunks", 1),
                    "preview": preview[:100] + "..." if len(preview) > 100 else preview,
                    "raw_file": meta.get("raw_file", "") or _get_raw_file_path(bid),
                }

        return {"total_items": len(seen), "total_chunks": total_count, "items": list(seen.values())}

    try:
        return await asyncio.to_thread(_sync_list)
    except Exception as e:
        raise RuntimeError(f"列出知识失败: {e}")


async def delete_knowledge(knowledge_id: str) -> Dict[str, str]:
    """
    删除知识。

    Args:
        knowledge_id (str): 知识 base_id。

    Returns:
        Dict[str, str]: 删除结果。
    """
    def _sync_delete():
        """同步执行，放到线程池避免阻塞事件循环。"""
        collection = get_collection()
        results = collection.get(where={"base_id": knowledge_id})

        if not results["ids"]:
            return {"message": f"未找到 ID '{knowledge_id}'"}

        collection.delete(ids=results["ids"])
        
        # 删除所有相关文件（Markdown + 附件）
        _delete_all_files(knowledge_id)
        
        msg = f"已删除 '{knowledge_id}'，共 {len(results['ids'])} 个片段（包括原始文件和附件）"
        return {"message": msg}

    try:
        return await asyncio.to_thread(_sync_delete)
    except Exception as e:
        raise RuntimeError(f"删除失败: {e}")


async def get_stats() -> Dict[str, Any]:
    """获取知识库统计。"""
    def _sync_stats():
        """同步执行，放到线程池避免阻塞事件循环。"""
        collection = get_collection()
        total = collection.count()
        all_data = collection.get() if total > 0 else {"metadatas": []}

        base_ids, tag_counts, source_counts = set(), {}, {}
        for meta in all_data.get("metadatas", []):
            base_ids.add(meta.get("base_id", "?"))
            for t in meta.get("tags", "").split(","):
                t = t.strip()
                if t:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            s = meta.get("source", "")
            if s:
                source_counts[s] = source_counts.get(s, 0) + 1

        return {"total_items": len(base_ids), "total_chunks": total, "tags": tag_counts, "sources": source_counts}

    try:
        return await asyncio.to_thread(_sync_stats)
    except Exception as e:
        raise RuntimeError(f"统计失败: {e}")


def warm_up():
    """
    启动时预热：初始化 SOPS 密钥 + ChromaDB + Embedding。
    在后台线程中运行，避免首次工具调用时的延迟。
    """
    try:
        logger.info("预热[1/4]: 获取 SOPS API Key...")
        _ = _get_embedding_api_key()
        logger.info("预热[2/4]: 创建 Embedding Function...")
        _ = _get_embedding_function()
        logger.info("预热[3/4]: 初始化 ChromaDB Client...")
        _ = _get_client()
        logger.info("预热[4/4]: 加载 Collection...")
        _ = get_collection()
        logger.info("预热: 全部完成!")
    except Exception as e:
        logger.warning(f"预热: 初始化失败（工具调用时会重试）: {e}")
