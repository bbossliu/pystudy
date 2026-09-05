import ast

from server.runner import RunResult

ID = 25
TITLE = "dsh 核心六包：tools——把关流水线与单调否决"

STORY = (
    "工具注册谁都会写，dsh 的精髓在执行流水线：guard 只能否决、不能放行。"
    "所以无论注册顺序如何，安全规则都不可能被后来的规则「翻案」——"
    "这是设计出来的单调性，不是巧合。这一关搭一条迷你把关流水线。"
)

KNOWLEDGE = """\
把关流水线与单调否决——安全性不依赖注册顺序。

1) 源码位置
  packages/core/tools/src/index.ts:712 的 ToolGuard 类型：
  返回字符串即否决，压根没有 allow 的形态；
  :748 的 guardReason()：第一个否决胜出。
  注意：dsh 源码是 TypeScript 写的，我们用 Python 模仿它的机制；
  TS 语法看不懂时，去查笔记里的《附录-TS语法速查》。

2) 单调否决
  guard 只能说「我反对」，不能说「我批准」。
  所以无论注册顺序如何，安全规则都不可能被后来的规则「翻案」——
  这是设计出来的单调性，不是巧合。

3) 对应笔记章节：03-tool-calls / 05-tool-runtime

4) Java 对照：Spring Security 的投票器
  AccessDecisionVoter 有赞成/反对/弃权三态，多数决可能被翻案；
  dsh 更狠——只有「反对票」存在，一张反对票就足够拦下。

5) 流水线位置
  guard 在工具真正执行之前跑：先问完所有守卫，全部不反对才调用。
  顺序不能反——先执行再问守卫，否决就形同虚设了。
"""

STARTER_CODE = """\
# 任务：实现 class ToolRuntime —— 工具把关流水线：guard 只能否决，不能放行
# 1. register(name, fn)：注册工具
# 2. guard(fn)：注册守卫，fn 收工具名，返回 None=不反对，返回字符串=否决理由
# 3. invoke(name)：先依次问所有 guard —— 任一否决就立刻返回 已否决：{理由}（第一个否决胜出）
#    全部不反对才真正调用工具并返回结果
# 期望输出：
# 已否决：高危操作

class ToolRuntime:
    def __init__(self):
        self.tools = {}
        self.guards = []

    def register(self, name, fn):
        self.tools[name] = fn

    def guard(self, fn):
        self.guards.append(fn)

    def invoke(self, name):
        for g in self.guards:
            reason = g(name)
            if reason is not None:
                return f"已否决：{___}"  # 填：否决理由（提示：reason）
        return self.tools[___]()  # 填：用哪个名字找工具（提示：name）

runtime = ToolRuntime()
runtime.register("删除文件", lambda: "已删除")

def allow_all(name):
    return ___  # 填：不反对（提示：None）

def danger_guard(name):
    if name == ___:  # 填：哪个工具算高危（提示："删除文件"）
        return "高危操作"
    return None

runtime.guard(allow_all)
runtime.guard(danger_guard)
print(runtime.invoke(___))  # 填：调用哪个工具（提示："删除文件"）
"""

SOLUTION = """\
class ToolRuntime:
    def __init__(self):
        self.tools = {}
        self.guards = []

    def register(self, name, fn):
        self.tools[name] = fn

    def guard(self, fn):
        self.guards.append(fn)

    def invoke(self, name):
        for g in self.guards:
            reason = g(name)
            if reason is not None:
                return f"已否决：{reason}"
        return self.tools[name]()

runtime = ToolRuntime()
runtime.register("删除文件", lambda: "已删除")

def allow_all(name):
    return None

def danger_guard(name):
    if name == "删除文件":
        return "高危操作"
    return None

runtime.guard(allow_all)
runtime.guard(danger_guard)
print(runtime.invoke("删除文件"))
"""

EXPECTED_OUTPUT = "已否决：高危操作"


def _find_invoke(tree: ast.AST) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ToolRuntime":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "invoke":
                    return item
    return None


def _calls_outside_loops(fn: ast.FunctionDef, fors: list[ast.For]) -> list[ast.Call]:
    inside = set()
    for loop in fors:
        for node in ast.walk(loop):
            inside.add(id(node))
    return [
        node for node in ast.walk(fn)
        if isinstance(node, ast.Call) and id(node) not in inside
    ]


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, "输出不对哦，期望打印一行：\n已否决：高危操作"
    tree = ast.parse(source)
    invoke = _find_invoke(tree)
    if invoke is None:
        return False, (
            "结果对了，但本关要求定义 class ToolRuntime（含 register / guard / invoke 方法），"
            "不能直接打印答案"
        )
    fors = [node for node in ast.walk(invoke) if isinstance(node, ast.For)]
    if not fors:
        return False, "invoke 里要先用 for 循环依次问所有 guard——流水线从守卫开始"
    outside_calls = _calls_outside_loops(invoke, fors)
    if not outside_calls:
        return False, (
            "invoke 里要在守卫放行之后真正调用工具（self.tools[name](...)）并返回结果"
        )
    first_loop = min(node.lineno for node in fors)
    first_call = min(node.lineno for node in outside_calls)
    if first_call < first_loop:
        return False, (
            "顺序反了！guard 循环必须出现在工具调用之前——"
            "先执行再问守卫，否决就形同虚设"
        )
    has_short_circuit = any(
        isinstance(node, (ast.Return, ast.Break))
        for loop in fors for node in ast.walk(loop)
    )
    if not has_short_circuit:
        return False, (
            "guard 否决后要立刻返回（return 或 break 短路）——"
            "第一个否决胜出，后面的 guard 不用再问"
        )
    return True, (
        "过关！guard 只能否决、不能放行——安全性不再依赖注册顺序，这是设计出来的。"
    )
