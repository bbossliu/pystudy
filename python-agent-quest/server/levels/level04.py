import ast

from server.runner import RunResult

ID = 4
TITLE = "if/elif：让 Agent 会做决定"

STORY = (
    "消息有结构了，但小K 还听不懂用户想干嘛——问天气和让写代码，它的反应一模一样。"
    "给它装一个意图路由器，让它学会做决定。"
)

KNOWLEDGE = """\
if/elif/else 对比 Java：冒号和缩进代替大括号，elif 就是 else if：
  Java:   if (s.contains("写")) { ... } else if (s.contains("天气")) { ... } else { ... }
  Python: if "写" in s:
              ...
          elif "天气" in s:
              ...
          else:
              ...

注意：
  - in 关键字判断包含，比 Java 的 str.contains() 更顺手
  - 缩进就是代码块，缩进错了会直接报错
  - Python 没有 switch（3.10+ 有 match，了解即可）
"""

STARTER_CODE = """\
# 任务：用 if/elif/else 给 agent 装一个意图路由器
# user_input 含「写」→ 打印：意图：写代码
# user_input 含「天气」→ 打印：意图：查天气
# 其他情况 → 打印：意图：闲聊
# 期望输出：意图：写代码

user_input = "帮我写个爬虫"

if ___:  # 提示：用 "写" in user_input 判断包含
    ___
elif ___:
    ___
else:
    ___
"""

SOLUTION = """\
user_input = "帮我写个爬虫"
if "写" in user_input:
    print("意图：写代码")
elif "天气" in user_input:
    print("意图：查天气")
else:
    print("意图：闲聊")
"""

EXPECTED_OUTPUT = "意图：写代码"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, "输出不对哦，期望打印：意图：写代码"
    tree = ast.parse(source)
    if_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.If)]
    if not if_nodes:
        return False, "结果对了，但本关要求用 if/elif/else 做判断，不能直接打印答案"
    has_elif = any(
        any(isinstance(branch, ast.If) for branch in node.orelse)
        for node in if_nodes
    )
    if not has_elif:
        return False, "要至少用一个 elif 来处理「查天气」的分支"
    has_in = any(
        isinstance(node, ast.Compare)
        and any(isinstance(op, ast.In) for op in node.ops)
        for node in ast.walk(tree)
    )
    if not has_in:
        return False, '判断包含请用 in 关键字，比如 "写" in user_input'
    return True, "过关！小K 会判断用户意图了。"
