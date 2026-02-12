# 🎯 最优开发策略：基础 → 进阶，一个项目两次蜕变

## 核心思路：不做两个项目，做一个项目的两个阶段

> **基础阶段的代码 100% 被进阶阶段复用**，一行不浪费。

```
阶段 A（基础，2-3小时）                阶段 B（中等，在A基础上加4-5小时）
┌──────────────────────┐             ┌──────────────────────────────┐
│ 第10题：API聚合封装     │  ──升级──→  │ 第21题：个性化知识管理智能体    │
│                      │             │                              │
│ ✅ 学会 MCP 模板流程   │             │ ✅ 新增 ChromaDB 向量数据库    │
│ ✅ 搞定 LLM 对话      │  直接复用→   │ ✅ 新增 RAG 检索增强生成       │
│ ✅ 搞定环境配置/Git    │  直接复用→   │ ✅ 新增文本分块处理            │
│ ✅ 熟悉 tool/core 写法 │             │ ✅ 最终提交这个版本            │
└──────────────────────┘             └──────────────────────────────┘
```

**为什么这是最优策略：**
- 阶段 A 的 `llm_service.py` 在阶段 B 直接用
- 阶段 A 的 config/Git/环境 在阶段 B 直接用
- 阶段 A 做完你就完全理解了 MCP 模板的开发流程
- 如果时间不够，交阶段 A 就是基础题；时间够就交阶段 B 拿高分

---

# ═══════════════════════════════════════════
# 阶段 A：基础题热身（第 10 题 - API 聚合封装）
# ═══════════════════════════════════════════

> **目标：** 2-3 小时跑通整个流程，做出一个能用的 MCP Server
> **成果：** 一个集成了 LLM 对话 + 天气查询 + 翻译的 MCP 服务器

---

## A-1: 环境准备（15分钟）

### 确认工具已安装

```powershell
python --version    # 需要 3.10+
uv --version        # 需要 uv
git --version       # 需要 Git
node --version      # 需要 Node.js（MCP Inspector 用）
```

如果缺少工具：
```powershell
# 安装 uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Git 和 Node.js 去官网下载安装
# https://git-scm.com
# https://nodejs.org
```

---

## A-2: 修改配置文件（10分钟）

### 修改 `config.yaml`

```yaml
server:
  name: YA_MCPServer_KnowledgeAgent
  name_zh: 个性化知识管理智能体
  author: 你的名字
  description: A personalized knowledge management agent with RAG-based intelligent Q&A.
  description_zh: 基于 RAG 的个性化知识管理智能体，支持知识存储、语义检索和智能问答。
  version: 0.1.0

transport:
  type: "sse"
  host: "127.0.0.1"
  port: 12345

logging:
  console:
    enabled: true
    level: "DEBUG"
  file:
    enabled: true
    level: "DEBUG"
    path: "logs/%Y-%m-%d_%H-%M-%S.log"
    rotation: "10 MB"
    retention: "7 days"
    compression: "zip"

# LLM 配置
llm:
  default_provider: "deepseek"
  deepseek:
    base_url: "https://api.deepseek.com"
    model: "deepseek-chat"
    max_tokens: 2048
    temperature: 0.7
  openai:
    model: "gpt-3.5-turbo"
    max_tokens: 2048
    temperature: 0.7

# 翻译配置
translate:
  base_url: "https://api.mymemory.translated.net"
```

> 💡 为什么直接用最终项目名？因为阶段 A 的代码会直接升级为阶段 B，不用改两次名字。

### 修改 `pyproject.toml`

```toml
[project]
name = "YA_MCPServer_KnowledgeAgent"
version = "0.1.0"
description = "A personalized knowledge management agent with RAG."
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "art>=6.5",
    "black>=25.9.0",
    "colorlog>=6.10.1",
    "httpx>=0.28.1",
    "mcp[cli]>=1.14.0",
    "pyyaml>=6.0.2",
    "ruff>=0.14.4",
    "openai>=1.0.0",
]
```

> ⚠️ 阶段 A 先不装 chromadb，保持依赖轻量，快速跑起来。

---

## A-3: Git 初始化 + 虚拟环境（10分钟）

```powershell
cd "d:\Syncthing Folder\Asus-Lenovo\School Projects\project_agent\YA_MCPServer_Template"

# Git 初始化
git init
git branch -M main
git add .
git commit -m "Initial Commit"

# 创建开发分支
git checkout -b dev main

# 创建虚拟环境
uv sync

# 激活
.venv\Scripts\activate

# 验证
python -c "import mcp; print('MCP OK')"
python -c "import openai; print('OpenAI OK')"
python -c "import httpx; print('HTTPX OK')"
```

---

## A-4: 运行模板验证环境（5分钟）

```powershell
uv run server.py
```

看到服务器启动信息就说明环境没问题。`Ctrl+C` 停止。

---

## A-5: 写第一个核心模块 `core/llm_service.py`（30分钟）

> 这是阶段 A 和阶段 B 都要用的核心模块，写一次永久复用。

创建文件 `core/llm_service.py`：

```python
"""
LLM 服务模块

提供以下功能：
- chat_with_llm: 调用 LLM API 进行对话（支持 DeepSeek / OpenAI）
"""

import os
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("llm_service")


async def chat_with_llm(
    message: str,
    system_prompt: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    调用 LLM API 进行对话。

    Args:
        message (str): 用户消息。
        system_prompt (Optional[str]): 系统提示词。
        provider (Optional[str]): LLM 提供商（"deepseek" 或 "openai"），默认读取配置。

    Returns:
        Dict[str, Any]: 对话结果，包含回复内容和 Token 使用信息。

    Raises:
        RuntimeError: 如果 API 调用失败。
        ValueError: 如果 provider 不合法。

    Example:
        {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "reply": "Python 的装饰器是...",
            "usage": {"prompt_tokens": 150, "completion_tokens": 200}
        }
    """
    if provider is None:
        provider = get_config("llm.default_provider", "deepseek")

    if provider not in ("deepseek", "openai"):
        raise ValueError(f"不支持的 LLM: {provider}，请使用 'deepseek' 或 'openai'")

    logger.info(f"调用 LLM [{provider}]，消息长度: {len(message)}")

    try:
        api_key = _get_api_key(provider)

        if provider == "deepseek":
            base_url = get_config("llm.deepseek.base_url", "https://api.deepseek.com")
            model = get_config("llm.deepseek.model", "deepseek-chat")
        else:
            base_url = None
            model = get_config("llm.openai.model", "gpt-3.5-turbo")

        max_tokens = get_config(f"llm.{provider}.max_tokens", 2048)
        temperature = get_config(f"llm.{provider}.temperature", 0.7)
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

        logger.info(f"LLM [{provider}] 回复成功，Token: {usage}")

        return {
            "provider": provider,
            "model": model,
            "reply": reply,
            "usage": usage,
        }
    except Exception as e:
        raise RuntimeError(f"LLM 调用失败 [{provider}]: {e}")


def _get_api_key(provider: str) -> str:
    """从环境变量获取 API Key。"""
    env_map = {
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    env_var = env_map.get(provider, "")
    key = os.environ.get(env_var)

    if not key:
        try:
            from modules.YA_Secrets.secrets_parser import get_secret
            key = get_secret(env_var.lower())
        except Exception:
            pass

    if not key:
        raise RuntimeError(f"未找到 {provider} 的 API Key，请设置环境变量 {env_var}")
    return key
```

---

## A-6: 写第二个核心模块 `core/weather_service.py`（15分钟）

创建文件 `core/weather_service.py`：

```python
"""
天气查询服务模块

提供以下功能：
- query_weather: 使用 wttr.in 免费 API 查询城市天气
"""

from typing import Dict, Any
import httpx
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("weather_service")


async def query_weather(city: str) -> Dict[str, Any]:
    """
    查询指定城市的当前天气信息。

    使用免费的 wttr.in API，无需 API Key。

    Args:
        city (str): 城市名称（支持中英文，如 "北京"、"London"）。

    Returns:
        Dict[str, Any]: 天气信息字典。

    Raises:
        RuntimeError: 如果天气 API 调用失败。

    Example:
        {
            "city": "北京",
            "temperature": "25°C",
            "feels_like": "27°C",
            "weather": "晴",
            "humidity": "40%",
            "wind": "NE 12km/h"
        }
    """
    logger.info(f"查询天气: {city}")

    try:
        url = f"https://wttr.in/{city}"
        params = {"format": "j1"}

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        current = data.get("current_condition", [{}])[0]

        # 尝试获取中文天气描述
        lang_zh = current.get("lang_zh", [])
        if lang_zh:
            weather_desc = lang_zh[0].get("value", "未知")
        else:
            desc_list = current.get("weatherDesc", [{}])
            weather_desc = desc_list[0].get("value", "未知") if desc_list else "未知"

        result = {
            "city": city,
            "temperature": f"{current.get('temp_C', 'N/A')}°C",
            "feels_like": f"{current.get('FeelsLikeC', 'N/A')}°C",
            "weather": weather_desc,
            "humidity": f"{current.get('humidity', 'N/A')}%",
            "wind": f"{current.get('winddir16Point', '')} {current.get('windspeedKmph', '')}km/h",
            "visibility": f"{current.get('visibility', 'N/A')}km",
        }

        logger.info(f"天气查询成功: {city} - {weather_desc} {result['temperature']}")
        return result

    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"天气 API 请求失败 (HTTP {e.response.status_code}): {e}")
    except Exception as e:
        raise RuntimeError(f"天气查询失败: {e}")
```

---

## A-7: 写第三个核心模块 `core/translate_service.py`（15分钟）

创建文件 `core/translate_service.py`：

```python
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
```

---

## A-8: 写 MCP Tools（30分钟）

### 创建 `tools/chat_tool.py`

```python
"""
智能对话工具，包括：
- smart_chat: 调用 LLM 进行对话
"""

from typing import Any, Dict, Optional
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="smart_chat",
    title="Smart Chat",
    description="调用大语言模型进行智能对话，支持 DeepSeek 和 OpenAI",
)
async def smart_chat(
    message: str,
    provider: str = "deepseek",
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """调用 LLM 进行智能对话。

    Args:
        message (str): 用户消息。
        provider (str): LLM 提供商（"deepseek" 或 "openai"），默认 "deepseek"。
        system_prompt (Optional[str]): 系统提示词。

    Returns:
        Dict[str, Any]: AI 回复和 Token 使用信息。
    """
    try:
        from core.llm_service import chat_with_llm
    except ImportError as e:
        raise RuntimeError(f"无法导入 LLM 模块: {e}")

    return await chat_with_llm(message=message, system_prompt=system_prompt, provider=provider)
```

### 创建 `tools/weather_tool.py`

```python
"""
天气查询工具，包括：
- weather_query: 查询城市天气
"""

from typing import Any, Dict
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="weather_query",
    title="Weather Query",
    description="查询指定城市的当前天气信息，支持中英文城市名，免费无需 Key",
)
async def weather_query(city: str) -> Dict[str, Any]:
    """查询城市天气。

    Args:
        city (str): 城市名称（如 "北京"、"上海"、"London"）。

    Returns:
        Dict[str, Any]: 温度、天气、湿度、风力等信息。
    """
    try:
        from core.weather_service import query_weather
    except ImportError as e:
        raise RuntimeError(f"无法导入天气模块: {e}")

    return await query_weather(city=city)
```

### 创建 `tools/translate_tool.py`

```python
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
```

---

## A-9: 设置 API Key & 测试（15分钟）

```powershell
# 设置 DeepSeek Key（国内直连，推荐）
$env:DEEPSEEK_API_KEY="你的Key"

# 启动服务器
uv run server.py
```

### 用 MCP Inspector 测试

新窗口：
```powershell
npx @anthropic/mcp-inspector
```

浏览器中连接 `http://127.0.0.1:12345/sse`，测试：
- `weather_query` → city: "北京" ✅
- `text_translate` → text: "你好", target_lang: "英文" ✅
- `smart_chat` → message: "你好" ✅

---

## A-10: Git 提交阶段 A（5分钟）

```powershell
git add .
git commit -m "feat: Phase A - LLM chat, weather query, translation tools"
```

---

## ✅ 阶段 A 完成！

此时你已经：
- [x] 理解了 MCP Server 模板的完整开发流程
- [x] 会写 `core/` 核心模块
- [x] 会写 `tools/` MCP 工具
- [x] 会用 MCP Inspector 测试
- [x] 有了可复用的 `llm_service.py`

**耗时约 2-3 小时。**

---

# ═══════════════════════════════════════════
# 阶段 B：进阶为中等题（第 21 题 - 知识管理智能体）
# ═══════════════════════════════════════════

> **目标：** 在阶段 A 的基础上，新增向量数据库 + RAG，升级为中等难度
> **新增工作量：** 4-5 小时
> **复用阶段 A 的：** llm_service.py、config.yaml、Git、环境、所有已有 Tools

---

## B-1: 新增依赖（5分钟）

修改 `pyproject.toml`，在 dependencies 里**新增一行**：

```toml
dependencies = [
    # ... 保留阶段 A 的所有依赖 ...
    "chromadb>=0.5.0",
]
```

然后：
```powershell
uv sync
# 验证
python -c "import chromadb; print('ChromaDB OK')"
```

> ChromaDB 首次导入会自动下载嵌入模型（~80MB），需要网络。

---

## B-2: 更新 `config.yaml`（5分钟）

在 `config.yaml` 末尾**追加**知识库配置（保留阶段 A 已有的配置不动）：

```yaml
# ===== 阶段 B 新增：知识管理配置 =====
knowledge:
  chromadb:
    persist_directory: "./data/chromadb"
    collection_name: "knowledge_base"
  chunking:
    chunk_size: 500
    chunk_overlap: 50
  retrieval:
    top_k: 5
    min_relevance: 0.3
```

在 `.gitignore` 中添加：
```
data/
```

---

## B-3: 新建 `core/document_processor.py`（20分钟）

文本分块模块，把长文本切成适合向量数据库存储的小片段。

```python
"""
文档处理模块

提供以下功能：
- split_text: 将长文本按固定大小切分为多个片段（支持重叠）
"""

from typing import List
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("document_processor")


def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[str]:
    """
    将长文本切分为多个片段。

    在句号、换行符等自然断点处优先切分。

    Args:
        text (str): 要切分的文本。
        chunk_size (int): 每个片段最大字符数，默认 500。
        chunk_overlap (int): 相邻片段重叠字符数，默认 50。

    Returns:
        List[str]: 切分后的文本片段列表。

    Raises:
        ValueError: 如果参数不合法。

    Example:
        >>> split_text("一段很长的文本...", chunk_size=100)
        ["一段很长的...", "...的文本接下来..."]
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size 必须大于 0，当前: {chunk_size}")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(f"chunk_overlap ({chunk_overlap}) 必须在 [0, {chunk_size}) 范围内")

    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    break_chars = ["\n\n", "\n", "。", "！", "？", ". ", "! ", "? ", "；"]
    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # 在后半段寻找自然断点
        best_break = -1
        for bc in break_chars:
            pos = text.rfind(bc, start + chunk_size // 2, end)
            if pos > best_break:
                best_break = pos + len(bc)

        if best_break > start:
            end = best_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - chunk_overlap

    logger.debug(f"文本分块: 原始={len(text)}字, 片段数={len(chunks)}")
    return chunks
```

---

## B-4: 新建 `core/knowledge_store.py`（40分钟）⭐ 核心

向量数据库操作封装，这是阶段 B 最重要的模块。

```python
"""
知识存储模块 - ChromaDB 向量数据库封装

提供以下功能：
- add_knowledge: 添加知识到向量数据库
- search_knowledge: 语义搜索知识
- list_knowledge: 列出知识条目
- delete_knowledge: 删除知识
- get_stats: 获取统计信息
"""

import uuid
from typing import Dict, Any, Optional
import chromadb
from modules.YA_Common.utils.config import get_config
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("knowledge_store")

_client: Optional[chromadb.PersistentClient] = None
_collection = None


def _get_client() -> chromadb.PersistentClient:
    """获取 ChromaDB 客户端（单例）"""
    global _client
    if _client is None:
        path = get_config("knowledge.chromadb.persist_directory", "./data/chromadb")
        logger.info(f"初始化 ChromaDB: {path}")
        _client = chromadb.PersistentClient(path=path)
    return _client


def get_collection():
    """获取知识库集合"""
    global _collection
    if _collection is None:
        name = get_config("knowledge.chromadb.collection_name", "knowledge_base")
        _collection = _get_client().get_or_create_collection(name=name)
        logger.info(f"集合 '{name}' 已加载，当前 {_collection.count()} 条")
    return _collection


async def add_knowledge(
    content: str,
    title: str = "",
    tags: str = "",
    source: str = "",
) -> Dict[str, Any]:
    """
    添加知识到向量数据库（自动分块 + 自动向量化）。

    Args:
        content (str): 知识内容文本。
        title (str): 标题。
        tags (str): 标签（逗号分隔，如 "python,编程"）。
        source (str): 来源（如 "课件"、"笔记"）。

    Returns:
        Dict[str, Any]: 添加结果，包含 ID 和分块数。

    Raises:
        RuntimeError: 如果添加失败。

    Example:
        {"id": "kb_a1b2c3d4", "title": "Python装饰器", "chunks_count": 2, "message": "知识添加成功"}
    """
    logger.info(f"添加知识: title='{title}', len={len(content)}")

    try:
        from core.document_processor import split_text
    except ImportError as e:
        raise RuntimeError(f"无法导入文档处理模块: {e}")

    try:
        collection = get_collection()
        chunk_size = get_config("knowledge.chunking.chunk_size", 500)
        chunk_overlap = get_config("knowledge.chunking.chunk_overlap", 50)
        chunks = split_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        base_id = f"kb_{uuid.uuid4().hex[:8]}"
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

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
            })

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info(f"添加成功: {base_id}, {len(chunks)} 个片段")

        return {
            "id": base_id,
            "title": title,
            "tags": tag_list,
            "chunks_count": len(chunks),
            "message": "知识添加成功",
        }
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

    try:
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
                formatted.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "title": results["metadatas"][0][i].get("title", ""),
                    "tags": results["metadatas"][0][i].get("tags", ""),
                    "source": results["metadatas"][0][i].get("source", ""),
                    "relevance": round(1 - dist, 4),
                })

        logger.info(f"搜索返回 {len(formatted)} 条")
        return {"query": query, "total_results": len(formatted), "results": formatted}
    except Exception as e:
        raise RuntimeError(f"搜索失败: {e}")


async def list_knowledge(tag_filter: str = "", limit: int = 20) -> Dict[str, Any]:
    """
    列出知识条目。

    Args:
        tag_filter (str): 标签过滤。
        limit (int): 最大返回数。

    Returns:
        Dict[str, Any]: 知识列表。
    """
    try:
        collection = get_collection()
        get_params = {"limit": limit}
        if tag_filter:
            get_params["where"] = {"tags": {"$contains": tag_filter}}

        results = collection.get(**get_params)

        seen = {}
        for i in range(len(results["ids"])):
            meta = results["metadatas"][i]
            bid = meta.get("base_id", results["ids"][i])
            if bid not in seen:
                preview = results["documents"][i]
                seen[bid] = {
                    "id": bid,
                    "title": meta.get("title", "未命名"),
                    "tags": meta.get("tags", ""),
                    "source": meta.get("source", ""),
                    "total_chunks": meta.get("total_chunks", 1),
                    "preview": preview[:100] + "..." if len(preview) > 100 else preview,
                }

        return {"total_items": len(seen), "total_chunks": collection.count(), "items": list(seen.values())}
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
    try:
        collection = get_collection()
        results = collection.get(where={"base_id": knowledge_id})

        if not results["ids"]:
            return {"message": f"未找到 ID '{knowledge_id}'"}

        collection.delete(ids=results["ids"])
        return {"message": f"已删除 '{knowledge_id}'，共 {len(results['ids'])} 个片段"}
    except Exception as e:
        raise RuntimeError(f"删除失败: {e}")


async def get_stats() -> Dict[str, Any]:
    """获取知识库统计。"""
    try:
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
    except Exception as e:
        raise RuntimeError(f"统计失败: {e}")
```

---

## B-5: 新建 `core/rag_service.py`（30分钟）⭐ RAG 核心

```python
"""
RAG (Retrieval-Augmented Generation) 服务模块

提供以下功能：
- ask_knowledge: 检索知识库 + LLM 生成回答
"""

from typing import Dict, Any, Optional
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

如果以上知识不包含答案，回答"根据现有知识库暂无相关信息，建议添加相关知识后再次提问。"
"""


async def ask_knowledge(
    question: str,
    top_k: int = 5,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    基于知识库的 RAG 智能问答。

    流程: 语义检索知识片段 → 拼接为上下文 → LLM 生成回答

    Args:
        question (str): 用户问题。
        top_k (int): 检索片段数，默认 5。
        provider (Optional[str]): LLM 提供商。

    Returns:
        Dict[str, Any]: 回答 + 引用来源。

    Raises:
        RuntimeError: 如果流程失败。

    Example:
        {
            "question": "Python装饰器怎么用？",
            "answer": "根据知识库...",
            "sources": [{"title": "Python装饰器", "relevance": 0.85}],
            "context_chunks_used": 3
        }
    """
    logger.info(f"RAG 问答: '{question[:50]}'")

    try:
        from core.knowledge_store import search_knowledge
    except ImportError as e:
        raise RuntimeError(f"无法导入知识模块: {e}")

    try:
        search_results = await search_knowledge(query=question, top_k=top_k)
    except Exception as e:
        raise RuntimeError(f"知识检索失败: {e}")

    results = search_results.get("results", [])
    if not results:
        return {
            "question": question,
            "answer": "知识库中暂无相关内容，请先用 add_knowledge 添加知识。",
            "sources": [],
            "context_chunks_used": 0,
        }

    # 过滤低相关度
    min_rel = get_config("knowledge.retrieval.min_relevance", 0.3)
    filtered = [r for r in results if r.get("relevance", 0) >= min_rel] or results[:2]

    # 构建上下文
    context_parts, sources = [], []
    for i, r in enumerate(filtered):
        context_parts.append(
            f"【知识{i+1}】(来源: {r.get('title', '未知')}, 相关度: {r.get('relevance', 0):.2f})\n{r['content']}"
        )
        sources.append({"title": r.get("title", "未知"), "relevance": r.get("relevance", 0)})

    system_prompt = RAG_SYSTEM_PROMPT.format(context="\n\n---\n\n".join(context_parts))

    try:
        from core.llm_service import chat_with_llm
    except ImportError as e:
        raise RuntimeError(f"无法导入 LLM 模块: {e}")

    try:
        llm_resp = await chat_with_llm(message=question, system_prompt=system_prompt, provider=provider)
    except Exception as e:
        raise RuntimeError(f"LLM 生成失败: {e}")

    logger.info(f"RAG 完成，使用 {len(filtered)} 个片段")

    return {
        "question": question,
        "answer": llm_resp["reply"],
        "sources": sources,
        "llm_provider": llm_resp["provider"],
        "context_chunks_used": len(filtered),
        "token_usage": llm_resp["usage"],
    }
```

---

## B-6: 新建知识管理 Tools（30分钟）

### 创建 `tools/knowledge_tool.py`

```python
"""
知识管理工具，包括：
- add_knowledge: 添加知识
- search_knowledge: 语义搜索
- list_knowledge: 列出知识
- delete_knowledge: 删除知识
"""

from typing import Any, Dict
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="add_knowledge",
    title="Add Knowledge",
    description="添加知识到个人知识库，支持笔记、文档、课件等，自动分块建立向量索引",
)
async def add_knowledge(
    content: str, title: str = "", tags: str = "", source: str = "",
) -> Dict[str, Any]:
    """添加知识到向量数据库。

    Args:
        content (str): 知识内容。
        title (str): 标题。
        tags (str): 标签（逗号分隔）。
        source (str): 来源。
    Returns:
        Dict[str, Any]: 添加结果。
    """
    try:
        from core.knowledge_store import add_knowledge as _add
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _add(content=content, title=title, tags=tags, source=source)


@YA_MCPServer_Tool(
    name="search_knowledge",
    title="Search Knowledge",
    description="语义搜索知识库，基于语义相似度而非关键词匹配",
)
async def search_knowledge(
    query: str, top_k: int = 5, tag_filter: str = "",
) -> Dict[str, Any]:
    """语义搜索知识库。

    Args:
        query (str): 搜索内容（自然语言）。
        top_k (int): 返回前 K 条。
        tag_filter (str): 标签过滤。
    Returns:
        Dict[str, Any]: 搜索结果。
    """
    try:
        from core.knowledge_store import search_knowledge as _search
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _search(query=query, top_k=top_k, tag_filter=tag_filter)


@YA_MCPServer_Tool(
    name="list_knowledge",
    title="List Knowledge",
    description="列出知识库中的所有知识条目",
)
async def list_knowledge(tag_filter: str = "", limit: int = 20) -> Dict[str, Any]:
    """列出知识。

    Args:
        tag_filter (str): 标签过滤。
        limit (int): 最大数量。
    Returns:
        Dict[str, Any]: 知识列表。
    """
    try:
        from core.knowledge_store import list_knowledge as _list
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _list(tag_filter=tag_filter, limit=limit)


@YA_MCPServer_Tool(
    name="delete_knowledge",
    title="Delete Knowledge",
    description="删除指定的知识条目",
)
async def delete_knowledge(knowledge_id: str) -> Dict[str, str]:
    """删除知识。

    Args:
        knowledge_id (str): 知识 ID。
    Returns:
        Dict[str, str]: 删除结果。
    """
    try:
        from core.knowledge_store import delete_knowledge as _del
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _del(knowledge_id=knowledge_id)
```

### 创建 `tools/qa_tool.py`

```python
"""
RAG 智能问答工具，包括：
- ask_knowledge: 基于知识库的智能问答
- knowledge_stats: 知识库统计
"""

from typing import Any, Dict, Optional
from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="ask_knowledge",
    title="Ask Knowledge (RAG)",
    description="基于知识库的智能问答：自动检索相关知识 + 大模型生成回答 + 标注来源",
)
async def ask_knowledge(
    question: str, top_k: int = 5, provider: Optional[str] = None,
) -> Dict[str, Any]:
    """RAG 智能问答。

    Args:
        question (str): 你的问题。
        top_k (int): 检索片段数。
        provider (Optional[str]): LLM 提供商。
    Returns:
        Dict[str, Any]: 回答 + 引用来源。
    """
    try:
        from core.rag_service import ask_knowledge as _ask
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await _ask(question=question, top_k=top_k, provider=provider)


@YA_MCPServer_Tool(
    name="knowledge_stats",
    title="Knowledge Stats",
    description="获取知识库统计信息：条目数、标签分布、来源分布",
)
async def knowledge_stats() -> Dict[str, Any]:
    """获取统计信息。"""
    try:
        from core.knowledge_store import get_stats
    except ImportError as e:
        raise RuntimeError(f"导入失败: {e}")
    return await get_stats()
```

---

## B-7: 新建 Resources & Prompts（20分钟）

### 创建 `resources/knowledge_resource.py`

```python
"""
知识库使用指南资源
"""

from resources import YA_MCPServer_Resource


@YA_MCPServer_Resource(
    "docs://knowledge-guide",
    name="knowledge_guide",
    title="Knowledge Guide",
    description="知识管理智能体使用指南",
    mime_type="text/markdown",
)
def get_knowledge_guide() -> str:
    """返回使用指南"""
    return """
# 📚 知识管理智能体使用指南

## 添加知识 → add_knowledge
- content: 内容（必填）| title: 标题 | tags: 标签 | source: 来源

## 语义搜索 → search_knowledge
- query: 搜索内容（自然语言）

## 智能问答 → ask_knowledge
- question: 你的问题（自动检索+LLM回答）

## 管理 → list_knowledge / delete_knowledge / knowledge_stats
"""
```

### 创建 `prompts/knowledge_prompt.py`

```python
"""
知识管理相关提示词
"""

from prompts import YA_MCPServer_Prompt


@YA_MCPServer_Prompt(
    name="knowledge_qa",
    title="Knowledge Q&A",
    description="知识问答助手提示词",
)
async def knowledge_qa_prompt(topic: str) -> str:
    """知识问答提示词。

    Args:
        topic (str): 提问主题。
    Returns:
        str: 提示词。
    """
    return f"请从知识库查找「{topic}」相关信息并回答。先用 search_knowledge 搜索，再用 ask_knowledge 问答。"


@YA_MCPServer_Prompt(
    name="knowledge_import",
    title="Knowledge Import",
    description="知识导入助手提示词",
)
async def knowledge_import_prompt(topic: str) -> str:
    """知识导入提示词。

    Args:
        topic (str): 知识主题。
    Returns:
        str: 提示词。
    """
    return f"我要导入关于「{topic}」的知识。请引导我提供内容，然后用 add_knowledge 添加。"
```

---

## B-8: 测试阶段 B（20分钟）

```powershell
$env:DEEPSEEK_API_KEY="你的Key"
uv run server.py
```

MCP Inspector 测试流程：

```
1️⃣ add_knowledge
   content: "Python 装饰器是一种修改函数行为的设计模式。
   本质上是一个高阶函数，接收函数作为参数返回新函数。
   常见内置装饰器：@property、@staticmethod、@classmethod。
   自定义装饰器示例：
   def timer(func):
       import time
       def wrapper(*args, **kwargs):
           start = time.time()
           result = func(*args, **kwargs)
           print(f'耗时: {time.time()-start:.2f}秒')
           return result
       return wrapper"
   title: "Python装饰器教程"
   tags: "python,编程,装饰器"
   source: "课件"

2️⃣ search_knowledge
   query: "如何给函数计时"  ← 没提"装饰器"，但能搜到！

3️⃣ ask_knowledge
   question: "Python中怎么在函数前后自动打印日志？"
   → 自动检索装饰器知识 + DeepSeek 生成回答

4️⃣ knowledge_stats
   → 查看统计

5️⃣ weather_query (阶段A的工具仍然可用！)
   city: "北京"
```

---

## B-9: 代码规范 + Git 提交（15分钟）

```powershell
# 代码规范
uv run ruff check .
uv run ruff check . --fix
uv run black .

# Git 提交
git add core/knowledge_store.py core/rag_service.py core/document_processor.py
git commit -m "feat: add ChromaDB knowledge store, RAG service, text chunking"

git add tools/knowledge_tool.py tools/qa_tool.py
git commit -m "feat: add knowledge management and RAG Q&A tools"

git add resources/knowledge_resource.py prompts/knowledge_prompt.py
git commit -m "feat: add knowledge guide resource and prompts"

git add config.yaml pyproject.toml .gitignore
git commit -m "chore: add chromadb dependency, knowledge config"
```

---

## B-10: 更新 README.md + 合并到 main（15分钟）

更新 README.md 内容（参照 `开发指南_完整流程.md` 的 Step 11），然后：

```powershell
git add README.md
git commit -m "docs: update README with full project documentation"

# 合并到 main
git checkout main
git merge dev
git log --oneline
```

---

## ✅ 全部完成！

### 最终项目包含：

| 来自阶段 | 文件 | 功能 |
|---------|------|------|
| A | `core/llm_service.py` | LLM 对话（DeepSeek/OpenAI）|
| A | `core/weather_service.py` | 天气查询 |
| A | `core/translate_service.py` | 文本翻译 |
| A | `tools/chat_tool.py` | 对话工具 |
| A | `tools/weather_tool.py` | 天气工具 |
| A | `tools/translate_tool.py` | 翻译工具 |
| **B** | **`core/knowledge_store.py`** | **向量数据库操作** |
| **B** | **`core/rag_service.py`** | **RAG 检索增强生成** |
| **B** | **`core/document_processor.py`** | **文本分块** |
| **B** | **`tools/knowledge_tool.py`** | **知识管理工具 ×4** |
| **B** | **`tools/qa_tool.py`** | **RAG 问答工具 ×2** |
| B | `resources/knowledge_resource.py` | 使用指南 |
| B | `prompts/knowledge_prompt.py` | 知识管理提示词 |

**总计：8 个 Tool + 3 个 Resource + 5 个 Prompt**

### 时间线总结：

```
Day 1（2-3小时）: 阶段 A
  → 环境搭建 + LLM/天气/翻译 三个工具搞定
  → 跑通 MCP Inspector 测试
  → ✅ 已经可以作为基础题提交

Day 2（4-5小时）: 阶段 B
  → 加 ChromaDB + RAG + 知识管理工具
  → 完善 README + Git 规范
  → ✅ 升级为中等难度提交，拿高分
```

---

## ⚡ 快速检查清单

提交前确认：

- [ ] `config.yaml` 项目名和描述已修改
- [ ] `pyproject.toml` 与 config.yaml 一致
- [ ] `README.md` 填写完整（组员信息、Tool/Resource/Prompt 列表）
- [ ] API Key 没有硬编码在代码里
- [ ] `data/` 在 .gitignore 中
- [ ] Git 有多次有意义的 commit
- [ ] main 分支包含最终代码
- [ ] `uv run ruff check .` 无报错
- [ ] MCP Inspector 测试全部通过
