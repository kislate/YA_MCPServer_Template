import os
from resources import YA_MCPServer_Resource
from typing import Any


@YA_MCPServer_Resource(
    "file:///README.md",  # 资源 URI
    name="readme_file",  # 资源 ID
    title="README.md",  # 资源标题
    description="返回项目的README.md",  # 资源描述
)
def get_readme() -> Any:
    """
    返回 README.md 文件内容

    Args:
        path (str): 文件路径。

    Returns:
        Any: 文件内容。
    """
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return {"error": "File not found"}


@YA_MCPServer_Resource(
    "file:///logs/{path}",  # 资源模板 URI
    name="get_server_logs",  # 资源 ID
    title="Get Server Logs",  # 资源标题
    description="返回日志文件内容",  # 资源描述
)
def get_server_logs(path: str) -> Any:
    """
    返回服务器日志文件的内容。
    这个资源可以被 MCP 客户端访问以获取文件内容。

    Args:
        path (str): 文件路径。

    Returns:
        Any: 文件内容。
    """
    try:
        LOG_ROOT = "logs/"
        full_path = os.path.normpath(os.path.join(LOG_ROOT, path))
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return {"error": "File not found"}
