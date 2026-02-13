# 网络搜索功能使用指南

## 功能概述

本 MCP 服务器新增了三个网络搜索工具，支持免费无需 API Key 的网络搜索和网页内容提取功能。

## 工具说明

### 1. web_search - 网络搜索

使用 DuckDuckGo 搜索引擎进行网络搜索，免费无需配置。

**示例用法：**
```python
# 基础搜索
result = await web_search(
    query="Python 最佳实践",
    max_results=5,
    region="cn-zh"
)

# 结果包含：
# - total: 结果总数
# - results: 结果列表，每项包含：
#   - rank: 排名
#   - title: 标题
#   - url: 链接
#   - snippet: 摘要
```

**参数说明：**
- `query`: 搜索关键词或问题（必需）
- `max_results`: 返回结果数量，默认 5，最多 20
- `region`: 搜索区域，默认 "cn-zh"（中国），可选：
  - `cn-zh`: 中国
  - `us-en`: 美国
  - `uk-en`: 英国
  - `jp-jp`: 日本

---

### 2. fetch_webpage - 网页内容提取

获取指定网页的完整文本内容，自动提取正文并去除广告、导航等无关内容。

**示例用法：**
```python
# 获取网页内容
result = await fetch_webpage(
    url="https://example.com/article",
    timeout=10,
    extract_main_content=True
)

# 结果包含：
# - url: 网页地址
# - title: 网页标题
# - content: 提取的文本内容
# - length: 内容长度（字符数）
```

**参数说明：**
- `url`: 网页地址，必须以 http:// 或 https:// 开头（必需）
- `timeout`: 请求超时时间（秒），默认 10
- `extract_main_content`: 是否仅提取正文内容，默认 True
  - True: 使用智能算法提取正文，去除导航、广告等
  - False: 提取所有可见文本

---

### 3. search_with_content - 搜索并获取内容

结合搜索和内容提取，一次性完成搜索并获取排名第一的网页完整内容。

**示例用法：**
```python
# 搜索并获取首个结果的完整内容
result = await search_with_content(
    query="如何学习机器学习",
    max_results=3
)

# 结果包含：
# - search_results: 搜索结果列表（同 web_search）
# - top_content: 第一个结果的完整网页内容（同 fetch_webpage）
#   - url
#   - title
#   - content
#   - length
```

**适用场景：**
- 需要深度了解某个主题
- 想要基于搜索结果进一步分析
- 结合 RAG 进行知识增强

---

## 实际应用场景

### 场景 1：实时信息查询
```python
# 查询最新新闻或实时信息
result = await web_search(
    query="2026年AI最新进展",
    max_results=10
)
```

### 场景 2：深度学习某个主题
```python
# 搜索并获取详细内容
result = await search_with_content(
    query="深度学习入门教程",
    max_results=3
)

# 可以将获取的内容添加到知识库
await add_knowledge(
    content=result["top_content"]["content"],
    title=result["top_content"]["title"],
    source=result["top_content"]["url"],
    tags=["深度学习", "教程"]
)
```

### 场景 3：网页内容归档
```python
# 提取并保存网页内容
webpage = await fetch_webpage(
    url="https://important-article.com",
    extract_main_content=True
)

# 添加到知识库永久保存
await add_knowledge(
    content=webpage["content"],
    title=webpage["title"],
    source=webpage["url"]
)
```

### 场景 4：增强 RAG 问答
```python
# 结合知识库和网络搜索
# 1. 先搜索知识库
kb_result = await search_knowledge(query="Python异步编程")

# 2. 如果知识库没有相关内容，搜索网络
if not kb_result["results"]:
    web_result = await search_with_content(
        query="Python异步编程教程",
        max_results=3
    )
    
    # 3. 将搜索到的内容添加到知识库
    await add_knowledge(
        content=web_result["top_content"]["content"],
        tags=["Python", "异步编程"]
    )
```

---

## 技术特点

1. **免费无限制**：使用 DuckDuckGo 搜索，无需 API Key，无调用次数限制
2. **智能内容提取**：使用 Trafilatura 算法，自动识别正文，去除广告和导航
3. **多语言支持**：支持全球多个区域的搜索
4. **异步高效**：基于 httpx 的异步请求，性能优秀
5. **容错机制**：网络异常时自动降级，确保服务可用

---

## 注意事项

1. **URL 格式**：使用 `fetch_webpage` 时，URL 必须包含协议（http:// 或 https://）
2. **超时设置**：访问慢速网站时，可适当增加 timeout 参数
3. **内容提取**：部分动态网站（JavaScript 渲染）可能无法提取完整内容
4. **搜索区域**：根据需求选择合适的搜索区域，获得更准确的结果
5. **内容长度**：某些网页内容可能很长，建议结合 LLM 进行摘要

---

## 故障排除

### 问题 1：搜索无结果
- 检查网络连接
- 尝试更换搜索关键词
- 更换搜索区域（region 参数）

### 问题 2：网页内容提取失败
- 确认 URL 格式正确
- 增加 timeout 参数
- 某些网站可能有反爬虫机制，尝试其他来源

### 问题 3：内容提取不完整
- 设置 `extract_main_content=False` 获取所有文本
- 可能是动态网站，考虑使用其他数据源

---

## 依赖说明

网络搜索功能依赖以下 Python 包（已在 pyproject.toml 中配置）：

```toml
dependencies = [
    "ddgs>=9.0.0",               # DuckDuckGo 搜索 (新包名)
    "beautifulsoup4>=4.12.0",     # HTML 解析
    "trafilatura>=2.0.0",         # 智能内容提取
    "lxml>=5.0.0",                # 解析器
]
```

安装命令：
```bash
uv sync
# 或
pip install ddgs beautifulsoup4 trafilatura lxml
```

> **注意**: `duckduckgo-search` 包已被重命名为 `ddgs`，请使用新包名。
