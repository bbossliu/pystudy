import ast

from server.runner import RunResult

ID = 19
TITLE = "Deep Agents 源码精读：Subagent 派发与上下文隔离"

STORY = (
    "主 agent 遇到复杂任务，一个人忙不过来，想找个「临时工」帮忙。"
    "但 Deep Agents 的设计很讲究：子代理只拿到任务描述，主对话的历史一个字都看不到——"
    "这就是上下文隔离。这一关我们实现派活的入口：task 工具。"
)

KNOWLEDGE = """\
Subagent 派发——上下文隔离的「临时工」。

1) 源码位置
  deepagents/middleware/subagents.py:732-794 的 _validate_and_prepare_state：
  派活给子代理时，它的初始状态里只有一条 [HumanMessage(description)]——
  主对话的历史一条都不带。这就是上下文隔离（context isolation）。

2) 为什么隔离？
  主对话可能聊了几万字，子代理只需要「查一下天气」这几个字。
  全量传过去既浪费 token 又干扰判断。隔离还有个好处：
  子代理跑偏了也不污染主对话——它的中间过程主 agent 根本看不见。

3) Java 对照：线程池提交任务
  executor.submit(new Task(description))——任务对象就是全部输入，
  而不是让线程去读共享内存里的全局状态。后者 bug 多、难排查，前者干净可控。

4) 结果怎么回来？
  子代理跑完，结果被包装成一条 tool 消息回到主对话：
  {"role": "tool", "content": 结果}。对主 agent 来说，
  派子代理和调普通工具长得一模一样——这就是 task 工具的伪装术。
"""

STARTER_CODE = """\
# 任务：实现 task(description, subagent_type)——主 agent 派活给子代理的入口
# 1. 调用 subagent_run(description)，把任务描述（且只有描述）交给子代理
# 2. 把结果包装成 dict {"role": "tool", "content": 结果} 返回，
#    子代理的成果会以 tool 消息的身份回到主对话
# 期望输出：
# {'role': 'tool', 'content': '子代理完成：查一下天气'}

def subagent_run(description):
    # 模拟一个子代理：只拿到任务描述，看不到主对话历史（上下文隔离）
    return f"子代理完成：{description}"

def task(description, subagent_type):
    result = ___(description)  # 填：把任务描述交给子代理执行
    return {"role": "___", "content": ___}  # 填：包装成 tool 消息

print(task("查一下天气", "weather-agent"))
"""

SOLUTION = """\
def subagent_run(description):
    return f"子代理完成：{description}"

def task(description, subagent_type):
    result = subagent_run(description)
    return {"role": "tool", "content": result}

print(task("查一下天气", "weather-agent"))
"""

EXPECTED_OUTPUT = "{'role': 'tool', 'content': '子代理完成：查一下天气'}"


def _returns_dict(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        if isinstance(node.value, ast.Dict):
            return True
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "dict"
        ):
            return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印一个 dict：\n"
            "{'role': 'tool', 'content': '子代理完成：查一下天气'}"
        )
    tree = ast.parse(source)
    task_fns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "task"
    ]
    if not task_fns:
        return False, "结果对了，但本关要求定义 task(description, subagent_type) 函数，不能直接打印答案"
    fn = task_fns[0]
    if len(fn.args.args) != 2:
        return False, "task 要接收两个参数：description 和 subagent_type——任务描述和子代理类型缺一不可"
    if not _returns_dict(fn):
        return False, (
            "task 要返回 dict {\"role\": \"tool\", \"content\": 结果}——"
            "子代理的成果是包装成 tool 消息回到主对话的"
        )
    return True, "过关！子代理只拿到任务描述、成果装成 tool 消息回来——上下文隔离拿捏了。"
