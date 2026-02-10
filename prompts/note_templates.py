from prompts import YA_MCPServer_Prompt
import datetime

@YA_MCPServer_Prompt(
    name="note_helper",
    title="智能笔记助手",
    description="引导 AI 以标准 Markdown 格式整理用户笔记"
)
def note_helper_prompt(raw_text: str):
    """
    当用户说'帮我记个笔记'时，AI 可以使用这个模板。
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return f"""
你现在是一个专业的笔记秘书。请将用户的输入内容整理为以下格式：

---
# 标题: [请根据内容起一个简短的标题]
- **记录时间**: {now}
- **关键词**: #笔记 #自动整理

## 📝 详细内容
{raw_text}

## 💡 后续行动
- [ ] (请根据内容提炼一个待办事项，如果没有则写'无')
---

**指令**:
整理完毕后，请**必须**询问用户：“是否需要我调用 `add_game_note` 工具将此笔记保存到文件中？”
"""