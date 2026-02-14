# 文档导入功能使用指南

## 功能概述

现在支持将 PDF 文档和网页直接导入到知识库中，自动转换为 Markdown 格式并建立向量索引。

## 新增工具

### 1. `import_pdf` - 导入 PDF 文档

**适用场景**：
- 学术论文
- 课程课件
- 电子书
- 技术文档

**使用示例**：

```python
# 导入 PDF 文档（自动提取标题）
await import_pdf(
    file_path="./papers/机器学习论文.pdf"
)

# 指定标题和标签
await import_pdf(
    file_path="./papers/deep_learning.pdf",
    title="深度学习基础",
    tags="机器学习,神经网络,AI"
)
```

**返回示例**：
```json
{
  "knowledge_id": "kb_12345678",
  "title": "深度学习基础",
  "tags": ["机器学习", "神经网络", "AI"],
  "chunks": 15,
  "pdf_pages": 45,
  "file_path": "D:/papers/deep_learning.pdf",
  "raw_file": "./data/raw/kb_12345678.md"
}
```

---

### 2. `import_webpage` - 导入网页笔记

**适用场景**：
- 技术博客
- 在线文档
- 新闻文章
- 教程网站

**使用示例**：

```python
# 导入技术博客
await import_webpage(
    url="https://example.com/article/python-best-practices"
)

# 指定标题和标签
await import_webpage(
    url="https://pytorch.org/tutorials/beginner/basics/intro.html",
    title="PyTorch 入门教程",
    tags="PyTorch,深度学习,教程"
)
```

**返回示例**：
```json
{
  "knowledge_id": "kb_87654321",
  "title": "PyTorch 入门教程",
  "tags": ["PyTorch", "深度学习", "教程"],
  "chunks": 8,
  "url": "https://pytorch.org/tutorials/beginner/basics/intro.html",
  "raw_file": "./data/raw/kb_87654321.md"
}
```

---

### 3. `import_document` - 智能导入（推荐）

**最简单的方式**：自动识别文档类型（PDF 或网页）

**使用示例**：

```python
# 自动识别 PDF
await import_document(source="./paper.pdf")

# 自动识别网页
await import_document(source="https://example.com/article")

# 带标签导入
await import_document(
    source="https://blog.example.com/ai-tutorial",
    tags="AI,教程"
)
```

---

## 工作流程

### PDF 导入流程
```
PDF 文件 → pypdfium2 提取文本 → 按页面分块 → 生成 Embedding → 存入 ChromaDB
         ↓
      保存为 Markdown（含 frontmatter）→ data/raw/{knowledge_id}.md
```

### 网页导入流程
```
URL → HTTP 抓取 HTML → html2text 转换 → Markdown 格式化 → 生成 Embedding → 存入 ChromaDB
     ↓
   保存为 Markdown（含 frontmatter）→ data/raw/{knowledge_id}.md
```

---

## 导入后的操作

导入后，文档会自动：

1. **分块建立索引** - 可通过 `search_knowledge` 语义搜索
2. **保存原始文件** - 存储在 `data/raw/` 目录
3. **自动标注来源** - 记录文件路径或 URL
4. **AI 生成元数据** - 如果未指定标题/标签，会自动生成

### 查询示例

```python
# 语义搜索导入的文档
await search_knowledge(
    query="深度学习的反向传播算法",
    top_k=5
)

# RAG 问答
await ask_knowledge(
    question="PyTorch 如何定义神经网络？"
)
```

---

## 技术细节

### 依赖库

| 库名 | 用途 | 版本要求 |
|------|------|----------|
| `pypdfium2` | PDF 文本提取 | ≥4.30.0 |
| `html2text` | HTML 转 Markdown | ≥2024.2.26 |
| `beautifulsoup4` | HTML 解析 | ≥4.12.0 |
| `httpx` | HTTP 请求 | ≥0.28.1 |

### 支持的文档类型

✅ **已支持**：
- PDF 文档 (`.pdf`)
- 网页 (HTTP/HTTPS URL)

🚧 **未来扩展**：
- PPT 课件 (`.pptx`)
- Word 文档 (`.docx`)
- Markdown 文件 (`.md`)
- 图片 OCR (`.jpg`, `.png`)

---

## 常见问题

### Q: PDF 提取的文本格式乱怎么办？
A: pypdfium2 会尽力保持原始格式，但复杂排版可能有偏差。可以手动调整后重新导入。

### Q: 网页转换 Markdown 后丢失了样式？
A: Markdown 只保留文本和链接，不保留 CSS 样式。这是预期行为。

### Q: 能否批量导入多个文档？
A: 当前需要逐个调用工具。可以编写脚本循环调用。

### Q: 如何删除导入的文档？
A: 使用 `delete_knowledge(knowledge_id)` 会同时删除向量和原始文件。

---

## 最佳实践

1. **合理使用标签** - 便于后续过滤和管理
2. **定期清理** - 删除过时的知识条目
3. **验证导入** - 导入后查看 `data/raw/` 确认格式正确
4. **备份数据** - 定期备份 `data/` 目录

---

## 示例：导入机器学习课程资料

```python
# 1. 导入课程 PDF
result1 = await import_pdf(
    file_path="./courses/ML_Lecture_1.pdf",
    title="机器学习第一讲",
    tags="机器学习,课程,数学基础"
)

# 2. 导入配套网页教程
result2 = await import_webpage(
    url="https://course.example.com/ml/lecture1",
    title="机器学习第一讲补充材料",
    tags="机器学习,课程"
)

# 3. 搜索相关知识
results = await search_knowledge(
    query="线性回归的数学原理",
    tag_filter="机器学习"
)

# 4. RAG 问答
answer = await ask_knowledge(
    question="请解释梯度下降算法的工作原理"
)
```

---

**Happy Learning! 🚀**
