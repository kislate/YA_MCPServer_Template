from typing import Any, Dict

from prompts import YA_MCPServer_Prompt


@YA_MCPServer_Prompt(
    name="greet_user",
    title="Greeting Prompt",
    description="生成一个问候消息",
)
async def hello_prompt(name: str) -> Dict[str, Any]:
    """一个简单的问候指令。

    Args:
        name (str): 用户的名字。

    Returns:
        Dict[str, str]: 包含问候语的字典。

    Example:
        {
            "greeting": "Hello, Alice!"
        }
    """
    return f"你好，{name}！欢迎使用 YA MCP Server。"
