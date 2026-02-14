# 🚀 快速开始：PDF 和网页笔记功能

## ✨ 新功能概述

现在你的知识管理系统支持：
- 📄 **PDF 文档导入**：自动提取文本，按页面分块
- 🌐 **网页笔记**：一键保存网页为 Markdown 格式
- 🤖 **智能识别**：自动判断文档类型并处理

## 📦 已安装的新依赖

```toml
pypdfium2>=4.30.0       # PDF 解析
html2text>=2024.2.26    # 网页转 Markdown
beautifulsoup4>=4.12.0  # HTML 解析
ddgs>=0.4.0             # DuckDuckGo 搜索
```

## 🎯 使用示例

### 1. 导入网页笔记

MCP 客户端（如 Claude Desktop）中：

```
我想保存这篇文章：https://pytorch.org/tutorials/beginner/basics/intro.html
```

系统会自动调用 `import_webpage` 工具：
```python
import_webpage(
    url="https://pytorch.org/tutorials/beginner/basics/intro.html"
)
```

**结果**：
- ✅ 网页内容转换为 Markdown
- ✅ 自动提取标题
- ✅ 建立向量索引
- ✅ 保存到 `data/raw/kb_xxxxx.md`

---

### 2. 导入 PDF 文档

准备一个 PDF 文件（例如：`my_paper.pdf`），然后：

```
请帮我导入这个 PDF：D:/Documents/my_paper.pdf
```

系统会调用 `import_pdf`：
```python
import_pdf(
    file_path="D:/Documents/my_paper.pdf"
)
```

**结果**：
- ✅ 提取所有页面文本
- ✅ 按页面组织内容
- ✅ 自动生成标题（从文件名）
- ✅ 建立向量索引

---

### 3. 智能导入（推荐）

最简单的方式，自动识别类型：

```
请导入：https://example.com/article
请导入：./documents/report.pdf
```

系统会自动判断是 URL 还是文件，并选择合适的解析器。

---

## 🔍 导入后的操作

### 语义搜索

```
在我的笔记中搜索"深度学习的反向传播"
```

系统会搜索所有导入的文档（包括 PDF 和网页）。

### RAG 问答

```
根据我导入的资料，解释一下 PyTorch 的张量操作
```

系统会：
1. 检索相关片段
2. 结合 LLM 生成回答
3. 标注来源（文件路径或 URL）

---

## 📁 文件组织

导入的文档会保存在：

```
data/
├── chromadb/           # 向量数据库
│   └── ...
└── raw/                # 原始 Markdown 文件
    ├── kb_12345678.md  # PDF 转换的笔记
    └── kb_87654321.md  # 网页笔记
```

每个文件都包含 YAML frontmatter：

```markdown
---
id: kb_12345678
title: 深度学习基础
tags: [机器学习, 神经网络]
source: PDF 文档：D:/papers/deep_learning.pdf
---

## 第 1 页

深度学习是机器学习的一个分支...

## 第 2 页

...
```

---

## 🛠️ MCP 工具列表

| 工具 | 用途 | 输入 |
|------|------|------|
| `import_pdf` | 导入 PDF | 文件路径 |
| `import_webpage` | 导入网页 | URL |
| `import_document` | 智能导入 | 文件路径或 URL |

---

## 💡 使用技巧

### 1. 批量导入课程资料

```
请帮我导入以下资料：
1. PDF：./ML_Course/lecture1.pdf
2. 网页：https://course.example.com/ml/intro
3. PDF：./ML_Course/lecture2.pdf
```

### 2. 添加标签便于管理

```
导入这个 PDF，并打上标签"机器学习,课程,第一讲"：
./courses/ml_lecture_1.pdf
```

### 3. 查看导入的文档

```
列出我所有的知识条目
```

或者按标签过滤：

```
显示所有标签为"机器学习"的笔记
```

---

## 🐛 故障排查

### PDF 文本提取失败

**原因**：PDF 是扫描版（图片）
**解决**：未来版本会支持 OCR

### 网页抓取失败

**原因**：需要登录或有反爬虫
**解决**：先手动复制内容，使用 `add_knowledge` 添加

### 依赖安装失败

```bash
# 重新同步依赖
uv sync

# 或手动安装
uv add pypdfium2 html2text beautifulsoup4
```

---

## 🎓 下一步

1. **尝试导入第一个文档**
2. **测试搜索功能**
3. **体验 RAG 问答**
4. **阅读完整文档**：[docs/document-import-guide.md](document-import-guide.md)

---

## 📚 相关文档

- [完整使用指南](document-import-guide.md)
- [项目 README](../README.md)
- [开发文档](开发指南.md)

---

**开始构建你的个人知识库吧！📖✨**
