import ast

from server.runner import RunResult

ID = 28
TITLE = "dsh 核心六包：agent-loop——轮次状态机（收口）"

STORY = (
    "总装关。ReAct 循环谁都能写个 while，dsh 的是状态机："
    "turn 内反复 step，每个边界都落事件——"
    "这就是为什么它的会话能回放、能恢复、能 fork。"
    "前五关的零件都在你手里了，这一关把它们装成一台整机。"
)

KNOWLEDGE = """\
轮次状态机——每个边界都落事件。

1) 源码位置
  packages/core/agent-loop/src/agent.ts:69 的 ReactLoopAgent（全仓核心单文件）；
  :253 的 turn()：一轮对话的边界；:339 的 step()：
  一个步骤 = 一次模型请求 + 它调用的工具。
  注意：dsh 源码是 TypeScript 写的，我们用 Python 模仿它的机制；
  TS 语法看不懂时，去查笔记里的《附录-TS语法速查》。

2) 状态机，不是 while 循环
  一轮（turn）= 零到多个步骤（step）。
  每个边界——turn 开始/结束、step 开始、模型消息、工具结果——
  都 append 一条事件。循环的每一圈都有据可查，
  所以会话能回放、能恢复、能 fork。

3) 对应笔记章节：02-agent-loop

4) Java 对照：状态机模式
  别用一个巨大的 while 把流程揉在一起；
  明确的状态 + 明确的迁移 + 每次迁移落事件，
  才是可观测、可恢复的循环。

5) 收口提示：前五关的零件都在这
  derive_messages 来自第 24 关（模型可见即已记录）；
  事件落账就是第 24 关的日志思想；
  工具执行可以再接上第 25 关的把关流水线；
  prompt 来自第 26 关的注册表；输入走第 27 关的 inbox。
  agent-loop 是唯一依赖前面全部五包的地方——所以它最后才登场。
"""

STARTER_CODE = """\
# 总装关：实现 agent_turn(log) —— 轮次状态机：turn 内反复 step，每个边界都落事件
#
# 下面这个 derive_messages 是你在第 24 关写的成品代码，直接复用：
def derive_messages(log):
    messages = []
    for event in log:
        if event["type"] == "user/message":
            messages.append({"role": "user", "content": event["content"]})
        elif event["type"] == "assistant/message" and event["content"]:
            messages.append({"role": "assistant", "content": event["content"]})
    return messages

# 脚本化 mock LLM（已写好，别改）：第一次要求调工具，第二次直接给答案
_llm_calls = {"n": 0}

def mock_llm(messages):
    _llm_calls["n"] += 1
    if _llm_calls["n"] == 1:
        return {"content": "", "tool_calls": ["查天气"]}
    return {"content": "北京今天晴", "tool_calls": []}

# 工具执行器（已写好，别改）
def run_tool(name):
    return {"tool": name, "result": "晴 25°C"}

# 任务：实现 agent_turn(log) —— 每个边界都往 log 里 append 事件
# 1. append 一条 turn/start
# 2. 循环：append step/start → 用 derive_messages 投影 log → 调 mock_llm
#    → 把模型回复 append 为 assistant/message 事件
#    → 若有 tool_calls：逐个 run_tool，把结果 append 为 tool/result 事件
#    → 没有 tool_calls 就跳出循环
# 3. append 一条 turn/end
# 期望输出（逐行打印日志里的事件类型）：
# turn/start
# step/start
# assistant/message
# tool/result
# step/start
# assistant/message
# turn/end

def agent_turn(log):
    log.append({"type": ___})  # 填：轮次开始事件（提示："turn/start"）
    while True:
        log.append({"type": ___})  # 填：步骤开始事件（提示："step/start"）
        messages = derive_messages(___)  # 填：投影谁（提示：log）
        reply = mock_llm(messages)
        log.append({"type": ___, "content": reply["content"]})  # 填：模型消息事件（提示："assistant/message"）
        if reply["tool_calls"]:
            for name in reply["tool_calls"]:
                result = run_tool(name)
                log.append({"type": ___, "content": result["result"]})  # 填：工具结果事件（提示："tool/result"）
        else:
            ___  # 填：没有工具调用就结束本轮（提示：break）
    log.append({"type": ___})  # 填：轮次结束事件（提示："turn/end"）

log = []
agent_turn(log)
for event in log:
    print(event[___])  # 填：打印事件的哪个字段（提示："type"）
"""

SOLUTION = """\
def derive_messages(log):
    messages = []
    for event in log:
        if event["type"] == "user/message":
            messages.append({"role": "user", "content": event["content"]})
        elif event["type"] == "assistant/message" and event["content"]:
            messages.append({"role": "assistant", "content": event["content"]})
    return messages

_llm_calls = {"n": 0}

def mock_llm(messages):
    _llm_calls["n"] += 1
    if _llm_calls["n"] == 1:
        return {"content": "", "tool_calls": ["查天气"]}
    return {"content": "北京今天晴", "tool_calls": []}

def run_tool(name):
    return {"tool": name, "result": "晴 25°C"}

def agent_turn(log):
    log.append({"type": "turn/start"})
    while True:
        log.append({"type": "step/start"})
        messages = derive_messages(log)
        reply = mock_llm(messages)
        log.append({"type": "assistant/message", "content": reply["content"]})
        if reply["tool_calls"]:
            for name in reply["tool_calls"]:
                result = run_tool(name)
                log.append({"type": "tool/result", "content": result["result"]})
        else:
            break
    log.append({"type": "turn/end"})

log = []
agent_turn(log)
for event in log:
    print(event["type"])
"""

EXPECTED_OUTPUT = (
    "turn/start\n"
    "step/start\n"
    "assistant/message\n"
    "tool/result\n"
    "step/start\n"
    "assistant/message\n"
    "turn/end"
)


def _find_agent_turn(tree: ast.AST) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "agent_turn":
            return node
    return None


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    # 事件序列逐行判定——序列本身就是本关的判定点
    expected_lines = EXPECTED_OUTPUT.splitlines()
    actual_lines = result.stdout.strip().splitlines()
    for i, expected in enumerate(expected_lines):
        if i >= len(actual_lines):
            return False, (
                f"事件序列不对：第 {i + 1} 行期望打印 {expected}，"
                f"但你的日志少了这条事件——每个边界都要落账"
            )
        if actual_lines[i].strip() != expected:
            return False, (
                f"事件序列不对：第 {i + 1} 行期望 {expected}，"
                f"实际是 {actual_lines[i].strip()}——"
                f"顺序是 turn/start → step → 模型消息 →（工具结果 →）step → … → turn/end"
            )
    if len(actual_lines) > len(expected_lines):
        return False, (
            f"事件序列不对：多打印了内容（第 {len(expected_lines) + 1} 行起："
            f"{actual_lines[len(expected_lines)].strip()}）——只打印日志里的事件类型"
        )
    tree = ast.parse(source)
    agent_turn = _find_agent_turn(tree)
    if agent_turn is None:
        return False, (
            "结果对了，但本关要求定义 agent_turn(log) 函数，不能直接打印答案"
        )
    if not any(isinstance(node, ast.While) for node in ast.walk(agent_turn)):
        return False, (
            "agent_turn 里要用 while 循环跑状态机——"
            "step 要跑几圈由模型说了算（有没有 tool_calls），不能提前写死"
        )
    if not any(isinstance(node, ast.Break) for node in ast.walk(agent_turn)):
        return False, (
            "while 里要有 break——模型不再调工具（tool_calls 为空）时结束本轮，"
            "这是状态机的出口"
        )
    return True, (
        "过关！六包全部到手——去读 dsh 真源码时，你会发现每个机制都见过。"
    )
