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
