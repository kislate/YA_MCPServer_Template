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
