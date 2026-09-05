import ast

from server.runner import RunResult

ID = 24
TITLE = "dsh 核心六包：session——事件日志与投影"

STORY = (
    "dsh 最硬的一条铁律：「模型可见即已记录」。"
    "模型看到的一切，必须先从 append-only 的事件日志里投影出来——"
    "日志是事实，视图是投影。这一关手写这个投影函数。"
)

KNOWLEDGE = """\
事件日志与投影——「模型可见即已记录」。

1) 源码位置
  packages/core/session/src/index.ts:724 的 deriveMessages()；
  surface.ts:83 的 deriveEventMessage() 纯函数：user/message 原样投影、
  空 assistant 丢弃、其余事件忽略。
  注意：dsh 源码是 TypeScript 写的，我们用 Python 模仿它的机制；
  TS 语法看不懂时，去查笔记里的《附录-TS语法速查》。

2) dsh 最硬的铁律
  模型看到的一切，必须先从 append-only 日志投影出来。
  日志是事实，视图是投影——回放、fork、崩溃恢复全部免费获得。

3) 对应笔记章节：04-session

4) Java 对照：事件溯源（Event Sourcing）
  Axon Framework 同款思想：不直接存「当前状态」，而是存一串事件，
  当前状态 = 把事件流 fold 出来的视图。改视图逻辑不用改数据，重放就行。

5) 空 assistant 为什么丢弃
  一次 step 里模型可能只调工具不说话（content 为空），这种消息投影给模型没意义，
  还会扰乱对话节奏——所以投影层直接过滤掉。
"""

STARTER_CODE = """\
# 任务：实现 derive_messages(log) —— 从事件日志「投影」出模型可见的消息列表
# 1. 遍历日志：type 为 "user/message" → {"role": "user", "content": ...}
# 2. type 为 "assistant/message" 且 content 非空 → {"role": "assistant", ...}（空内容要丢弃！）
# 3. 其他事件（turn/start、step/start、tool/result……）一律忽略
# 期望输出：
# user: 你好
# assistant: 你好！我是小K
# user: 帮我查天气

def derive_messages(log):
    messages = []
    for event in log:
        if event["type"] == ___:  # 填：哪种事件是用户消息（提示："user/message"）
            messages.append({"role": "user", "content": event["content"]})
        elif event["type"] == "assistant/message" and event[___]:  # 填：哪个字段非空才投影（提示："content"）
            messages.append({"role": ___, "content": event["content"]})  # 填：这个角色叫什么（提示："assistant"）
    return messages

log = [
    {"type": "turn/start"},
    {"type": "user/message", "content": "你好"},
    {"type": "assistant/message", "content": "你好！我是小K"},
    {"type": "user/message", "content": "帮我查天气"},
    {"type": "step/start"},
    {"type": "assistant/message", "content": ""},
    {"type": "tool/result", "content": "晴 25°C"},
    {"type": "turn/end"},
]

for msg in derive_messages(log):
    print(f"{___}: {___}")  # 填：消息的 role 和 content（提示：msg["role"]、msg["content"]）
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

log = [
    {"type": "turn/start"},
    {"type": "user/message", "content": "你好"},
    {"type": "assistant/message", "content": "你好！我是小K"},
    {"type": "user/message", "content": "帮我查天气"},
    {"type": "step/start"},
    {"type": "assistant/message", "content": ""},
    {"type": "tool/result", "content": "晴 25°C"},
    {"type": "turn/end"},
]

for msg in derive_messages(log):
    print(f"{msg['role']}: {msg['content']}")
"""

EXPECTED_OUTPUT = "user: 你好\nassistant: 你好！我是小K\nuser: 帮我查天气"


def _derive_fns(tree: ast.AST) -> list[ast.FunctionDef]:
    return [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "derive_messages"
    ]


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印三行（空 assistant 消息要丢弃，turn/step 事件要忽略）：\n"
            "user: 你好\n"
            "assistant: 你好！我是小K\n"
            "user: 帮我查天气"
        )
    tree = ast.parse(source)
    fns = _derive_fns(tree)
    if not fns:
        return False, "结果对了，但本关要求定义 derive_messages(log) 函数，不能直接打印答案"
    if not any(
        isinstance(node, ast.For) for fn in fns for node in ast.walk(fn)
    ):
        return False, (
            "derive_messages 里要用 for 循环遍历日志——"
            "投影就是把事件流一条条 fold 成视图，别用推导式一把梭"
        )
    if not any(
        isinstance(node, ast.If) for fn in fns for node in ast.walk(fn)
    ):
        return False, (
            "derive_messages 里要有 if 分支——按事件类型分类、把空 assistant 丢弃，"
            "靠的就是条件判断"
        )
    return True, (
        "过关！日志是事实，消息是投影——回放、fork、恢复都从这一层免费长出来。"
    )
