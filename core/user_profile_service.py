"""
用户画像服务模块

读写 data/memory/user_profile.json，为 LLM 提供个性化上下文。
提供以下功能：
- get_profile: 读取完整画像
- get_profile_context: 生成注入 prompt 的简洁描述字符串
- update_profile_field: 更新某个字段
- record_topic: 记录话题访问频次
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("user_profile_service")

PROFILE_PATH = Path("./data/memory/user_profile.json")

_DEFAULT_PROFILE: Dict[str, Any] = {
    "interests": [],
    "level": "未知",
    "preferences": [],
    "frequent_topics": {},
    "updated_at": "",
}


def _load() -> Dict[str, Any]:
    """从磁盘读取画像，不存在则返回默认值。"""
    if not PROFILE_PATH.exists():
        return _DEFAULT_PROFILE.copy()
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"读取用户画像失败，使用默认值: {e}")
        return _DEFAULT_PROFILE.copy()


def _save(profile: Dict[str, Any]) -> None:
    """将画像写入磁盘。"""
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    profile["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    PROFILE_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def get_profile() -> Dict[str, Any]:
    """读取完整用户画像。"""
    return _load()


def get_profile_context() -> str:
    """
    生成一段简洁的中文描述，可直接注入 LLM system prompt。
    无画像信息时返回空字符串。
    """
    p = _load()

    parts: List[str] = []

    level = p.get("level", "")
    if level and level != "未知":
        parts.append(f"用户级别：{level}")

    interests = p.get("interests", [])
    if interests:
        shown = interests[:6]
        parts.append(f"兴趣领域：{', '.join(shown)}")

    prefs = p.get("preferences", [])
    if prefs:
        parts.append(f"回答偏好：{'; '.join(prefs[:4])}")

    freq = p.get("frequent_topics", {})
    if freq:
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
        parts.append(f"常见话题：{', '.join(t for t, _ in top)}")

    if not parts:
        return ""

    return "## 用户个性化信息\n" + "\n".join(f"- {p}" for p in parts)


def update_profile_field(field: str, value: Any) -> Dict[str, Any]:
    """
    更新画像中的某个顶层字段。

    Args:
        field (str): 字段名，如 "level"、"preferences"、"interests"。
        value (Any): 新值。

    Returns:
        Dict[str, Any]: 更新后的画像。
    """
    profile = _load()
    profile[field] = value
    _save(profile)
    logger.info(f"用户画像字段已更新: {field}")
    return profile


def record_topic(topic: str, increment: int = 1) -> None:
    """
    记录一个话题的访问次数（用于频次统计）。

    Args:
        topic (str): 话题名称。
        increment (int): 增量，默认 1。
    """
    profile = _load()
    freq = profile.setdefault("frequent_topics", {})
    freq[topic] = freq.get(topic, 0) + increment
    _save(profile)
