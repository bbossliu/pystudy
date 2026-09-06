import ast

from server.runner import RunResult

ID = 2
TITLE = "list：给 Agent 装对话记忆"

STORY = (
    "小K 会自我介绍了，但它有个致命问题：每句话说完就忘，根本不记得你们聊过什么。"
    "真正的 agent 需要记忆——先给它装一个对话历史列表，把每轮对话都存下来。"
)

KNOWLEDGE = """\
list 就是 Python 的动态数组，对比 Java 的 ArrayList：

```plaintext
  Java:   List<String> messages = new ArrayList<>();
          messages.add("你好");
  Python: messages = []            # 不用声明泛型，不用 new
          messages.append("你好")  # 直接 append
```

常用操作：

```plaintext
  len(messages)   # 长度，对比 Java 的 messages.size()
  messages[0]     # 按下标取值，和 Java 一样从 0 开始
```
"""

STARTER_CODE = """\
# 任务：依次往 messages 里 append 三条消息（system 自我介绍、user 提问、assistant 回答）
# 期望输出（三行，顺序不能变）：
# [system] 你是小K，一个代码助手。
# [user] 你能帮我写代码吗？
# [assistant] 当然可以！

messages = []  # 对话历史列表，已为你建好

___  # 1. append 系统消息："[system] 你是小K，一个代码助手。"
___  # 2. append 用户提问："[user] 你能帮我写代码吗？"
___  # 3. append 助手回答："[assistant] 当然可以！"

# 逐条打印（这个 for 循环是成品，第 5 关才细讲，你不用动）
for msg in messages:
    print(msg)
"""

SOLUTION = """\
messages = []
messages.append("[system] 你是小K，一个代码助手。")
messages.append("[user] 你能帮我写代码吗？")
messages.append("[assistant] 当然可以！")
for msg in messages:
    print(msg)
"""

EXPECTED_OUTPUT = "[system] 你是小K，一个代码助手。\n[user] 你能帮我写代码吗？\n[assistant] 当然可以！"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望按顺序打印三条消息：\n"
            "[system] 你是小K，一个代码助手。\n"
            "[user] 你能帮我写代码吗？\n"
            "[assistant] 当然可以！"
        )
    tree = ast.parse(source)
    has_list = any(
        isinstance(node, ast.List)
        or (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "list")
        for node in ast.walk(tree)
    )
    if not has_list:
        return False, "结果对了，但本关要求用 list 来存消息，试试 messages = [] 的写法"
    has_append = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
        for node in ast.walk(tree)
    )
    if not has_append:
        return False, "结果对了，但要用 .append() 逐条把消息加进列表，别一次性写死"
    return True, "过关！小K 有记忆了，聊过的每句话都存进了列表。"
