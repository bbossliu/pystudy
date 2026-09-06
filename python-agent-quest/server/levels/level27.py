import ast

from server.runner import RunResult

ID = 27
TITLE = "dsh 核心六包：agent/inbox——先写日志后改状态"

STORY = (
    "agent 的收件箱随时可能崩：进程一挂，内存里的队列就没了。"
    "崩溃后怎么恢复？inbox 的每次变更都先把「做了什么修改」记进事件日志，"
    "再改内存——重放日志就能原地复活。这一关亲手实现这个顺序。"
)

KNOWLEDGE = """\
先写日志后改状态——顺序就是性命。

1) 源码位置
  packages/core/agent/src/inbox.ts:25 的 class Inbox；
  :186-187 是关键两行：先往事件日志 append 一条
  agent/inbox/spliced 事件，再改内存里的投影。
  注意：dsh 源码是 TypeScript 写的，我们用 Python 模仿它的机制；
  TS 语法看不懂时，去查笔记里的《附录-TS语法速查》。

2) 归属修正
  笔记把 inbox 归到了 core/agent-loop——其实它在 core/agent 包里
  （agent/src/inbox.ts）。读源码时别找错地方。
  对应笔记：整体架构 ④ 节（输入统一走 inbox）。

3) 为什么顺序不能反
  先改内存再写日志：改完内存、还没落日志时崩了，
  这次变更就永远丢了——重放日志恢复出的队列是错的。
  先写日志再改内存：写完日志就崩了也不怕，
  重放时把这次变更再做一遍，结果一致。

4) Java 对照：数据库 WAL（预写日志）
  MySQL 的 redo log 同款：先写日志、再改数据页，
  崩溃后拿日志重做。inbox 就是把这个思想搬到了 agent 的输入队列上。

5) replay 是纯函数式重建
  从空队列开始，把事件日志逐条重做（add 入队、remove 移除），
  得到的队列必须和内存里的一模一样——这就是「日志是事实」的检验标准。

6) 题外语法：@classmethod
  replay 不操作某个具体 Inbox 实例，而是「凭空造一个新的」——
  这种「属于类、不属于实例」的方法用 @classmethod 声明，
  第一个参数 cls 就是类本身（对照 Java 的 static 方法，
  区别是 Python 会把类显式传进来）。
"""

STARTER_CODE = """\
# 任务：实现 class Inbox —— 先写事件日志，再改内存队列
# 1. append(item)：先往 events 记 {"op": "add", "item": item}，再把 item 放进 queue
# 2. claim()：先往 events 记 {"op": "remove", "item": 队首}，再弹出队首并返回
# 3. @classmethod replay(cls, events)：从事件日志重建队列（add 入队、remove 移除）
# 期望输出：
# 当前队列：['消息2']
# 重放恢复：['消息2']

class Inbox:
    def __init__(self):
        self.events = []
        self.queue = []

    def append(self, item):
        # 顺序是性命：先写日志，再改内存
        self.events.append({"op": "add", "item": ___})  # 填：记下什么（提示：item）
        self.queue.append(___)  # 填：把什么放进队列（提示：item）

    def claim(self):
        item = self.queue[0]
        self.events.append({"op": "remove", "item": ___})  # 填：记下要移除谁（提示：item）
        self.queue.pop(___)  # 填：弹出哪个位置（提示：0）
        return item

    @classmethod
    def replay(cls, events):
        inbox = cls()
        for event in events:
            if event["op"] == "add":
                inbox.queue.append(event["item"])
            elif event["op"] == ___:  # 填：哪种操作是移除（提示："remove"）
                inbox.queue.remove(event["item"])
        return inbox

inbox = Inbox()
inbox.append("消息1")
inbox.append("消息2")
inbox.claim()
print(f"当前队列：{inbox.queue}")
restored = Inbox.replay(inbox.___)  # 填：拿什么来重放（提示：events）
print(f"重放恢复：{restored.queue}")
"""

SOLUTION = """\
class Inbox:
    def __init__(self):
        self.events = []
        self.queue = []

    def append(self, item):
        self.events.append({"op": "add", "item": item})
        self.queue.append(item)

    def claim(self):
        item = self.queue[0]
        self.events.append({"op": "remove", "item": item})
        self.queue.pop(0)
        return item

    @classmethod
    def replay(cls, events):
        inbox = cls()
        for event in events:
            if event["op"] == "add":
                inbox.queue.append(event["item"])
            elif event["op"] == "remove":
                inbox.queue.remove(event["item"])
        return inbox

inbox = Inbox()
inbox.append("消息1")
inbox.append("消息2")
inbox.claim()
print(f"当前队列：{inbox.queue}")
restored = Inbox.replay(inbox.events)
print(f"重放恢复：{restored.queue}")
"""

EXPECTED_OUTPUT = "当前队列：['消息2']\n重放恢复：['消息2']"


def _find_inbox(tree: ast.AST) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Inbox":
            return node
    return None


def _find_method(cls: ast.ClassDef, name: str) -> ast.FunctionDef | None:
    for item in cls.body:
        if isinstance(item, ast.FunctionDef) and item.name == name:
            return item
    return None


def _is_events_append(call: ast.Call) -> bool:
    # 只认 self.events.append(...) 形态：func 是 append 属性，挂在 xxx.events 上
    f = call.func
    return (
        isinstance(f, ast.Attribute) and f.attr == "append"
        and isinstance(f.value, ast.Attribute) and f.value.attr == "events"
    )


def _is_queue_mutation(call: ast.Call) -> bool:
    # 只认 self.queue.append/pop/remove/insert(...) 形态：对内存投影的修改
    f = call.func
    return (
        isinstance(f, ast.Attribute)
        and f.attr in ("append", "pop", "remove", "insert")
        and isinstance(f.value, ast.Attribute) and f.value.attr == "queue"
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行（claim 拿走「消息1」后只剩「消息2」，"
            "重放日志要恢复出一样的队列）：\n"
            "当前队列：['消息2']\n"
            "重放恢复：['消息2']"
        )
    tree = ast.parse(source)
    inbox_cls = _find_inbox(tree)
    if inbox_cls is None:
        return False, (
            "结果对了，但本关要求定义 class Inbox（含 events 日志和 queue 队列），"
            "不能直接打印答案"
        )
    append_fn = _find_method(inbox_cls, "append")
    if append_fn is None:
        return False, "Inbox 里要有 append(item) 方法——入队变更从这里开始"
    events_calls = [
        node for node in ast.walk(append_fn)
        if isinstance(node, ast.Call) and _is_events_append(node)
    ]
    if not events_calls:
        return False, (
            "append 里要把变更记进 events 日志（self.events.append({...})）——"
            "日志是恢复的唯一依据"
        )
    queue_calls = [
        node for node in ast.walk(append_fn)
        if isinstance(node, ast.Call) and _is_queue_mutation(node)
    ]
    if not queue_calls:
        return False, "append 里记完日志还要真的改内存队列（self.queue.append(item)）"
    first_event = min(node.lineno for node in events_calls)
    first_queue = min(node.lineno for node in queue_calls)
    if first_queue < first_event:
        return False, (
            "顺序反了！必须先写 events 日志、再改 queue——"
            "先改内存再写日志，中间一崩这次变更就永远丢了（想想数据库的 WAL）"
        )
    replay_fn = _find_method(inbox_cls, "replay")
    if replay_fn is None:
        return False, "要提供 replay——从事件日志重建队列，这才是「先写日志」的意义"
    is_classmethod = any(
        isinstance(dec, ast.Name) and dec.id == "classmethod"
        for dec in replay_fn.decorator_list
    )
    if not is_classmethod:
        return False, (
            "replay 要加 @classmethod——它是从日志「造出一个新 Inbox」的工厂，"
            "不该依赖已有实例"
        )
    return True, (
        "过关！先写日志再改内存——崩溃后重放 events，队列原地复活。"
        "这就是 WAL，也是 dsh「日志是事实」的又一次落地。"
    )
