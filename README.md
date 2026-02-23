## YA_MCPServer_KnowledgeAgent

基于 RAG（检索增强生成）的个性化知识管理智能体，支持知识存储、语义检索、智能问答、多语言翻译和网络搜索。

### 组员信息

| 姓名 | 学号 | 分工 | 备注 |
| :--: | :--: | :--: | :--: |
| 李宗锴 | U202414755 | 文档解析模块（PDF / PPTX / DOCX / 网页）、RAG 检索增强生成核心管线开发、ChromaDB 向量知识库模块 | 无 |
| 郑博远 | U202414771 |项目架构设计与 MCP Server 框架搭建 、批量导入与知识导出功能、网络搜索与网页抓取模块、SOPS密钥管理 | 无 |
| 董哲 | U202414746 | DeepSeek / SiliconFlow LLM 服务集成、多语言翻译服务、用户画像模块、工具注册与 Prompts 设计 | 无 |

### 快速开始

**前置要求：** Python 3.13+、[uv](https://docs.astral.sh/uv/)、Node.js（可选，用于 MCP Inspector）

**1. 克隆仓库（含子模块）**
```bash
git clone --recurse-submodules https://github.com/kislate/YA_MCPServer_Template.git
cd YA_MCPServer_Template
```

**2. 安装依赖**
```bash
uv sync
```

**3. 配置 API 密钥**

编辑 `env.yaml`，填入以下密钥（本地开发可直接写明文，加密方式见 [docs/encrypt.md](docs/encrypt.md)）：

| 密钥名 | 用途 | 获取地址 |
| :----: | :--: | :------: |
| `deepseek_api_key` | 大模型对话 / RAG 问答 / 翻译 | [platform.deepseek.com](https://platform.deepseek.com/) |
| `siliconflow_api_key` | BAAI/bge-m3 Embedding 向量化 | [cloud.siliconflow.cn](https://cloud.siliconflow.cn/) |

**4. 启动服务器**
```bash
uv run server.py
```

默认使用 STDIO 模式。如需 SSE（HTTP）模式，在 `config.yaml` 中将 `transport.type` 改为 `sse` 并配置 `host` / `port`。

**5. 接入 MCP 客户端（以 Claude Desktop / Cursor 为例）**
```json
{
  "mcpServers": {
    "KnowledgeAgent": {
      "command": "uv",
      "args": ["run", "server.py"],
      "cwd": "/path/to/YA_MCPServer_Template"
    }
  }
}
```

**6. 调试（可选）**
```bash
npx @modelcontextprotocol/inspector uv run server.py
```

### Tool 列表

| 工具名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| `add_knowledge` | 添加知识到个人知识库，自动分块建立向量索引，保存原始 Markdown | `content`(知识内容), `title`(标题,可留空AI生成), `tags`(标签,可留空), `source`(来源,可留空) | 知识 ID、标题、标签、分块数、原始文件路径 | title/tags/source 留空时由 DeepSeek 自动生成 |
| `get_knowledge` | 获取指定 ID 笔记的 Markdown 原文及附件信息 | `knowledge_id`(知识ID) | Markdown 原文、附件信息 | - |
| `update_knowledge` | 更新知识条目的内容、标题或标签 | `knowledge_id`(知识ID), `content`(新内容,可留空), `title`(新标题,可留空), `tags`(新标签,可留空) | 更新结果 | 仅改标题/标签不重新向量化；改内容自动重建索引 |
| `search_knowledge` | 语义搜索知识库，基于向量相似度匹配 | `query`(搜索内容), `top_k`(返回条数,默认5), `tag_filter`(标签过滤) | 匹配结果列表（含相似度分数、原始文件路径） | 使用 BAAI/bge-m3 Embedding |
| `list_knowledge` | 列出知识库中的所有知识条目 | `tag_filter`(标签过滤), `limit`(最大数量,默认100) | 知识条目列表（ID、标题、标签、来源） | - |
| `delete_knowledge` | 删除指定的知识条目（含所有分块和原始文件） | `knowledge_id`(知识ID) | 删除状态 | - |
| `export_knowledge` | 将知识库导出为本地文件 | `tag_filter`(标签过滤), `fmt`(格式: markdown/zip,默认markdown), `output_path`(输出路径,可留空) | 导出文件路径、条目数 | zip 格式含原始附件 |
| `update_user_profile` | 更新用户偏好画像，影响 RAG 问答个性化 | `field`(字段: interests/level/preferences), `value`(新值) | 更新后的画像 | 列表字段用逗号分隔 |
| `import_pdf` | 导入 PDF 文档到知识库，自动提取文本内容，按页面分块 | `file_path`(PDF文件路径), `title`(标题,可留空), `tags`(标签,可留空) | 知识 ID、标题、页数、分块数、文件路径 | 支持学术论文、课件、电子书等 |
| `import_pptx` | 导入 PPTX 演示文稿到知识库，提取幻灯片文本和表格 | `file_path`(PPTX文件路径), `title`(标题,可留空), `tags`(标签,可留空) | 知识 ID、标题、幻灯片数、分块数 | 支持课件、报告、培训材料等 |
| `import_docx` | 导入 DOCX Word 文档到知识库，保留文档结构 | `file_path`(DOCX文件路径), `title`(标题,可留空), `tags`(标签,可留空) | 知识 ID、标题、段落数、表格数 | 支持报告、论文、手册等 |
| `import_webpage` | 导入网页为 Markdown 笔记，自动抓取并转换格式 | `url`(网页URL), `title`(标题,可留空), `tags`(标签,可留空) | 知识 ID、标题、URL、分块数 | 支持技术博客、文档、文章等 |
| `import_document` | 智能导入文档，自动识别 PDF / PPTX / DOCX / 网页 | `source`(文件路径或URL), `title`(标题,可留空), `tags`(标签,可留空) | 知识 ID、文档类型、元数据 | 通用接口，自动选择解析器 |
| `batch_import_documents` | 批量导入整个文件夹内的文档到知识库 | `folder_path`(文件夹路径), `tags`(标签,可留空), `recursive`(递归子目录,默认False), `file_types`(格式过滤,可留空) | 成功列表、失败列表、汇总统计 | 支持 pdf/pptx/docx |
| `ask_knowledge` | RAG 智能问答：自动检索相关知识 → 大模型生成回答 → 标注来源 | `question`(问题), `top_k`(检索片段数,默认5), `provider`(LLM提供商) | AI 回答、引用来源、Token 用量 | 无匹配知识时直接由 DeepSeek 回答 |
| `knowledge_stats` | 获取知识库统计信息 | 无 | 条目数、分块数、标签分布、来源分布 | - |
| `smart_chat` | 调用 DeepSeek 大模型进行智能对话 | `message`(用户消息), `system_prompt`(系统提示词,可选) | AI 回复、模型名称、Token 用量 | 不经过知识库，纯 LLM 对话 |
| `text_translate` | 多语言文本翻译 | `text`(待翻译文本), `target_lang`(目标语言,默认"英文"), `source_lang`(源语言,默认"auto") | 原文、译文、语言对 | LLM 优先翻译，失败时降级 MyMemory |
| `get_supported_languages` | 获取翻译支持的语言列表 | 无 | 语言名-代码映射表 | 支持中英日韩法德西俄等 |
| `web_search` | 使用 DuckDuckGo 搜索网络内容 | `query`(搜索关键词), `max_results`(返回数量,默认5), `region`(搜索区域,默认wt-wt全球) | 搜索结果列表（含排名、标题、URL、摘要） | 免费无需 API Key，支持全球搜索 |
| `fetch_webpage` | 获取指定网页的完整文本内容 | `url`(网页地址), `timeout`(超时秒数,默认10), `extract_main_content`(提取正文,默认True) | 网页信息（标题、内容、长度） | 自动去除广告、导航等无关内容 |
| `search_with_content` | 搜索并自动获取首个结果的完整内容 | `query`(搜索关键词), `max_results`(搜索数量,默认3) | 搜索结果 + 首个网页完整内容 | 适合深度了解某个主题 |
| `search_and_save` | 搜索网络内容并自动存入知识库 | `query`(搜索关键词), `max_results`(保存条数,默认3), `tags`(标签,可留空), `save_all`(默认False) | 保存结果汇总（知识 ID、标题） | 每条网页单独保存为知识条目 |

### Resource 列表

| 资源名称 | 功能描述 | URI | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| `knowledge_guide` | 知识管理智能体使用指南 | `docs://knowledge-guide` | Markdown 格式使用文档 | MIME: text/markdown |

### Prompts 列表

| 指令名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| `greet_user` | 生成问候消息 | `name`(用户名字) | 格式化问候语 | 模板自带示例 |
| `knowledge_qa` | 知识问答助手提示词 | `topic`(提问主题) | 引导 RAG 问答的系统提示词 | - |
| `knowledge_import` | 知识导入助手提示词 | `topic`(知识主题) | 引导批量导入知识的提示词 | - |

### 项目结构

```
├── server.py                 # MCP Server 入口，支持 STDIO / SSE 两种传输方式
├── config.yaml               # 全局配置（服务器、传输、日志、LLM、知识库、翻译）
├── setup.py                  # 环境初始化钩子
├── env.yaml                  # SOPS 加密的密钥文件
├── .sops.yaml                # SOPS 加密规则（age 公钥列表）
├── core/                     # 核心业务逻辑
│   ├── knowledge_store.py    # ChromaDB 向量数据库封装（增删查 + Embedding + 原始文件管理）
│   ├── rag_service.py        # RAG 检索增强生成管线（语义检索 → 上下文构建 → LLM 回答）
│   ├── llm_service.py        # DeepSeek LLM 服务（对话 + AI 元数据自动生成）
│   ├── document_processor.py # 文本分块（自然断点优先，支持中英文标点）
│   ├── file_parser.py        # 文档解析器（PDF、网页转 Markdown）
│   ├── translate_service.py  # 翻译服务（LLM 优先 + MyMemory 降级）
│   └── web_search_service.py # DuckDuckGo 搜索 + 网页内容提取
├── tools/                    # MCP 工具定义（23 个工具）
│   ├── knowledge_tool.py     # 知识管理工具（增删查改导出+用户画像）
│   ├── document_tool.py      # 文档导入工具（PDF、PPTX、DOCX、网页、批量）
│   ├── qa_tool.py            # RAG 问答 + 统计工具
│   ├── chat_tool.py          # DeepSeek 直接对话工具
│   ├── translate_tool.py     # 翻译工具
│   └── web_search_tool.py    # 网络搜索 + 网页内容提取 + 搜索存库
├── prompts/                  # MCP 提示词模板（3 个）
│   ├── hello_prompt.py       # 问候提示词（模板示例）
│   └── knowledge_prompt.py   # 知识问答 / 导入助手提示词
├── resources/                # MCP 资源（1 个）
│   └── knowledge_resource.py # 使用指南文档资源
├── data/                     # 运行时数据（已 gitignore）
│   ├── chromadb/             # ChromaDB 持久化目录
│   └── raw/                  # 原始 Markdown 文件（带 YAML frontmatter）
├── modules/                  # Git 子模块
│   ├── YA_Common/            # 公共工具库（配置、日志、中间件、MCP 基类）
│   └── YA_Secrets/           # SOPS 密钥管理（加密/解密脚本）
└── docs/                     # 项目文档
```

### config.yaml 额外配置说明

| 配置项 | 说明 |
| :----: | :--: |
| `llm.deepseek` | DeepSeek 大模型配置（base_url / model / max_tokens / temperature） |
| `translate.base_url` | MyMemory 翻译 API 地址 |
| `knowledge.chromadb` | ChromaDB 持久化路径和集合名 |
| `knowledge.embedding` | SiliconFlow OpenAI 兼容接口参数（provider / base_url / model） |
| `knowledge.chunking` | 文本分块参数（chunk_size=1000 / chunk_overlap=100） |
| `knowledge.retrieval` | 检索参数（top_k=5 / min_relevance=0.3） |

### 其他需要说明的情况

**SOPS 密钥变量：**

| 密钥名 | 用途 |
| :----: | :--: |
| `deepseek_api_key` | DeepSeek 大模型 API 密钥，用于智能对话和 RAG 问答 |
| `siliconflow_api_key` | 硅基流动 (SiliconFlow) API 密钥，用于 BAAI/bge-m3 Embedding 向量化 |

**关于深度学习框架和模型：**

- **未使用** PyTorch、TensorFlow 等深度学习框架
- **未在本地运行**任何机器学习 / 深度学习模型
- Embedding 通过 SiliconFlow 远程 API 调用 BAAI/bge-m3 模型（1024 维），无需本地下载模型文件
- LLM 通过 DeepSeek 远程 API 调用 deepseek-chat 模型
