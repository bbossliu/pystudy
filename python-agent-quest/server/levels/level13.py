import ast

from server.runner import RunResult

ID = 13
TITLE = "终关：组装完整 Agent"

STORY = (
    "所有零件都齐了——prompt、记忆、路由、循环、容错、工具、并发。"
    "最后一关：把它们组装成一个真正能跑的 agent，完成一次完整的对话。"
)

KNOWLEDGE = """\
终关没有新语法，盘点一下你给小K 装上的零件：

```plaintext
  第 1 关   f-string     → 拼 system prompt
  第 2/3 关 list / dict  → 对话记忆（就是 OpenAI API 的消息格式）
  第 4 关   if/elif      → 意图路由
  第 5 关   for / 推导式  → think → act 主循环
  第 6 关   def          → 封装 LLM 调用
  第 7 关   try/except   → 工具调用容错
  第 8 关   文件 + json   → 记忆持久化
  第 9 关   class        → Tool 与 Agent 对象
  第 10 关  装饰器        → @tool 自动注册
  第 11 关  模块          → 拆分项目文件
  第 12 关  async/await  → 并发调工具
```

接真实 API 只差一步：把 mock_llm 换成 openai 的调用——

```python
  from openai import OpenAI
  client = OpenAI()
  resp = client.chat.completions.create(model="gpt-4o-mini", messages=self.memory)
```
生产级 agent 的核心也就是这套结构，再加上更多工具和状态管理——
LangGraph 这类框架干的正是这件事。
"""

STARTER_CODE = """\
# 终关任务：完成 Agent 类，让它完成一次完整对话
# chat 要做的事：
#   1. 用户消息存进记忆（dict：{"role": "user", "content": 内容}）
#   2. 调 mock_llm 生成回复
#   3. 回复也存进记忆（dict，role 为 "assistant"）
#   4. 返回回复
# 期望输出：
# 用户：你好
# 小K：mock 回复
# 用户：记住我叫小明
# 小K：mock 回复
# 记忆条数：4

def mock_llm(prompt):
    return "mock 回复"

class Agent:
    def __init__(self, name):
        self.name = name
        self.memory = ___  # 填：一个空列表

    def chat(self, user_input):
        self.memory.append(___)  # 用户消息，dict 形式
        reply = mock_llm(user_input)
        self.memory.append(___)  # 助手回复，dict 形式
        return reply

agent = Agent("小K")
for user_input in ["你好", "记住我叫小明"]:
    print(f"用户：{user_input}")
    print(f"{agent.name}：{agent.chat(user_input)}")

print(f"记忆条数：{len(agent.memory)}")
"""

SOLUTION = """\
def mock_llm(prompt):
    return "mock 回复"

class Agent:
    def __init__(self, name):
        self.name = name
        self.memory = []

    def chat(self, user_input):
        self.memory.append({"role": "user", "content": user_input})
        reply = mock_llm(user_input)
        self.memory.append({"role": "assistant", "content": reply})
        return reply

agent = Agent("小K")
for user_input in ["你好", "记住我叫小明"]:
    print(f"用户：{user_input}")
    print(f"{agent.name}：{agent.chat(user_input)}")

print(f"记忆条数：{len(agent.memory)}")
"""

EXPECTED_OUTPUT = "用户：你好\n小K：mock 回复\n用户：记住我叫小明\n小K：mock 回复\n记忆条数：4"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印五行：\n"
            "用户：你好\n小K：mock 回复\n用户：记住我叫小明\n小K：mock 回复\n记忆条数：4"
        )
    tree = ast.parse(source)
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    agent = classes.get("Agent")
    if agent is None:
        return False, "结果对了，但本关要把对话逻辑组织进 class Agent，不能散装或直接打印答案"
    methods = {node.name for node in agent.body if isinstance(node, ast.FunctionDef)}
    if "chat" not in methods:
        return False, "Agent 还缺 chat 方法——对话入口要封装在 Agent 里"
    has_role_dict = any(
        isinstance(node, ast.Dict)
        and any(isinstance(key, ast.Constant) and key.value == "role" for key in node.keys)
        for node in ast.walk(tree)
    )
    if not has_role_dict:
        return False, '记忆里的消息要用 dict 存（带 "role" 键），这正是真实 LLM API 的消息格式'
    return True, "通关！你造出了一个完整的 agent——把 mock_llm 换成真实 API 调用，它就能上生产了。"
