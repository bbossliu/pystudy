from server.runner import RunResult

ID = 1
TITLE = "变量与 f-string"

STORY = (
    "你的 agent 刚刚诞生，但它还不会自我介绍。给它拼一个 system prompt："
    "它叫「小K」，角色是「代码助手」。"
)

KNOWLEDGE = """\
Python 变量不需要声明类型：
  Java:   String name = "小K";
  Python: name = "小K"

f-string 是 Python 最常用的字符串拼接方式，在引号前加 f，变量直接写进 {}：
  Java:   String.format("你是%s，一个%s。", name, role)
  Python: f"你是{name}，一个{role}。"
"""

STARTER_CODE = """\
# 任务：定义变量 name 和 role，用 f-string 拼出 system prompt 并打印
# 期望输出：你是小K，一个代码助手。

name = ___  # 填：你的名字「小K」
role = ___  # 填：你的角色「代码助手」

system_prompt = ___  # 用 f-string 拼接 name 和 role
print(system_prompt)
"""

SOLUTION = """\
name = "小K"
role = "代码助手"
system_prompt = f"你是{name}，一个{role}。"
print(system_prompt)
"""

EXPECTED_OUTPUT = "你是小K，一个代码助手。"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, f"输出不对哦，期望打印：{EXPECTED_OUTPUT}"
    if 'f"' not in source and "f'" not in source:
        return False, '结果对了，但本关要求用 f-string 拼接，试试 f"...{name}..." 的写法'
    return True, "过关！你的 agent 会自我介绍了。"
