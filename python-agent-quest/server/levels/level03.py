import ast

from server.runner import RunResult

ID = 3
TITLE = "dict：消息要有结构"

STORY = (
    "记忆列表能存消息了，但一堆纯字符串混在一起，根本分不清哪句是谁说的。"
    "把消息升级成结构化字典——这也正是 OpenAI API 里一条消息的真实格式。"
)

KNOWLEDGE = """\
dict 是键值对，对比 Java 的 Map：

```plaintext
  Java:   Map<String, String> msg = Map.of("role", "user", "content", "你好");
  Python: msg = {"role": "user", "content": "你好"}   # 字面量直接写
```

取值用下标，对比 Java 的 get：

```plaintext
  Java:   msg.get("role")
  Python: msg["role"]       # 也可以 msg.get("role")
```

顺便说：{"role": "user", "content": "..."} 就是真实 LLM API 的消息结构。
"""

STARTER_CODE = """\
# 任务：构造一个字典 message（包含 role 和 content 两个字段），然后分别打印出来
# 期望输出：
# 角色：user
# 内容：今天天气怎么样

message = ___  # 填：{"role": "user", "content": "今天天气怎么样"}

print(f"角色：{___}")  # 填：从 message 里取 role
print(f"内容：{___}")  # 填：从 message 里取 content
"""

SOLUTION = """\
message = {"role": "user", "content": "今天天气怎么样"}
print(f"角色：{message['role']}")
print(f"内容：{message['content']}")
"""

EXPECTED_OUTPUT = "角色：user\n内容：今天天气怎么样"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, "输出不对哦，期望打印：\n角色：user\n内容：今天天气怎么样"
    tree = ast.parse(source)
    has_dict = any(isinstance(node, ast.Dict) for node in ast.walk(tree))
    if not has_dict:
        return False, (
            '结果对了，但本关要求用 dict 存消息，'
            '试试 message = {"role": ..., "content": ...} 的写法'
        )
    has_lookup = any(
        isinstance(node, ast.Subscript)
        or (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get")
        for node in ast.walk(tree)
    )
    if not has_lookup:
        return False, '结果对了，但要用 message["role"] 或 message.get("role") 从字典里取值，别直接打印字面量'
    return True, "过关！消息有了结构，这正是真实 LLM API 的样子。"
