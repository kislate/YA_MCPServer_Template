## YA_MCPServer_KnowledgeAgent

基于 RAG（检索增强生成）的个性化知识管理智能体，支持知识存储、语义检索、智能问答和多语言翻译。

### 组员信息

| 姓名 | 学号 | 分工 | 备注 |
| :--: | :--: | :--: | :--: |
|      |      |      |      |
|      |      |      |      |
|      |      |      |      |

### Tool 列表

| 工具名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| `add_knowledge` | 添加知识到个人知识库，自动分块建立向量索引，保存原始 Markdown | `content`(知识内容), `title`(标题,可留空AI生成), `tags`(标签,可留空), `source`(来源,可留空) | 知识 ID、标题、标签、分块数、原始文件路径 | title/tags/source 留空时由 DeepSeek 自动生成 |
| `search_knowledge` | 语义搜索知识库，基于向量相似度匹配 | `query`(搜索内容), `top_k`(返回条数,默认5), `tag_filter`(标签过滤) | 匹配结果列表（含相似度分数、原始文件路径） | 使用 BAAI/bge-m3 Embedding |
| `list_knowledge` | 列出知识库中的所有知识条目 | `tag_filter`(标签过滤), `limit`(最大数量,默认20) | 知识条目列表（ID、标题、标签、来源） | - |
| `delete_knowledge` | 删除指定的知识条目（含所有分块和原始文件） | `knowledge_id`(知识ID) | 删除状态 | - |
| `ask_knowledge` | RAG 智能问答：自动检索相关知识 → 大模型生成回答 → 标注来源 | `question`(问题), `top_k`(检索片段数,默认5), `provider`(LLM提供商) | AI 回答、引用来源、Token 用量 | 无匹配知识时直接由 DeepSeek 回答 |
| `knowledge_stats` | 获取知识库统计信息 | 无 | 条目数、分块数、标签分布、来源分布 | - |
| `smart_chat` | 调用 DeepSeek 大模型进行智能对话 | `message`(用户消息), `system_prompt`(系统提示词,可选) | AI 回复、模型名称、Token 用量 | 不经过知识库，纯 LLM 对话 |
| `text_translate` | 多语言文本翻译 | `text`(待翻译文本), `target_lang`(目标语言,默认"英文"), `source_lang`(源语言,默认"auto") | 原文、译文、语言对 | 使用 MyMemory 免费 API，免 Key |
| `get_supported_languages` | 获取翻译支持的语言列表 | 无 | 语言名-代码映射表 | 支持中英日韩法德西俄等 |

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
│   └── translate_service.py  # MyMemory 翻译服务
├── tools/                    # MCP 工具定义（9 个工具）
│   ├── knowledge_tool.py     # 知识管理工具（增删查）
│   ├── qa_tool.py            # RAG 问答 + 统计工具
│   ├── chat_tool.py          # DeepSeek 直接对话工具
│   └── translate_tool.py     # 翻译工具
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
