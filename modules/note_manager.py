import os
import json
# 从模板的核心装饰器里导入注册工具和资源的函数
from prompts import YA_MCPServer_Prompt
from resources import YA_MCPServer_Resource
from tools import YA_MCPServer_Tool
# 打印一句话，方便我们在终端看到它是否被加载了
print(">>> [成功] 正在加载笔记管理模块...")

# 定义笔记存放的文件夹路径
NOTES_DIR = "my_notes"

# --- 工具部分：创建笔记 ---
@YA_MCPServer_Tool()
def add_note(title: str, content: str) -> str:
    """
    创建一个新的笔记文件。
    Args:
        title: 笔记文件名 (例如: 'math.txt')
        content: 笔记的具体内容
    """
    try:
        if not os.path.exists(NOTES_DIR):
            os.makedirs(NOTES_DIR)
            
        file_path = os.path.join(NOTES_DIR, title)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"笔记《{title}》已存入知识库！"
    except Exception as e:
        return f"保存失败: {str(e)}"

# --- 资源部分：读取笔记 ---
@YA_MCPServer_Resource("notes://list")
def list_notes() -> str:
    """列出所有已保存的笔记名称"""
    try:
        if not os.path.exists(NOTES_DIR) or not os.listdir(NOTES_DIR):
            return "目前还没有任何笔记。"
        files = os.listdir(NOTES_DIR)
        return "你的笔记列表：\n" + "\n".join(files)
    except Exception as e:
        return f"读取列表失败: {str(e)}"

@YA_MCPServer_Resource("note://{filename}")
def read_note_content(filename: str) -> str:
    """根据文件名读取具体的笔记内容"""
    try:
        file_path = os.path.join(NOTES_DIR, filename)
        if not os.path.exists(file_path):
            return f"找不到文件: {filename}"
        with open(file_path, "r", encoding="utf-8") as f:
            return f"--- {filename} 的内容 ---\n{f.read()}"
    except Exception as e:
        return f"读取内容失败: {str(e)}"