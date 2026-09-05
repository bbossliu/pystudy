import ast

from server.runner import RunResult

ID = 23
TITLE = "dsh 核心六包：scope——分层可见性"

STORY = (
    "你的 agent 想要一份「私人配置」：全局默认所有 agent 共享，"
    "但每个 agent 可以只覆盖自己在乎的几项，互不干扰。"
    "dsh 的 scope 包干的就是这件事——一条父子链，近端覆盖远端。"
    "这一关先用 Python 把这个机制模仿出来。"
)

KNOWLEDGE = """\
分层可见性——近端覆盖远端。

1) 源码位置
  packages/core/scope/src/store.ts:159 的 ScopedLayers；
  :208 的 merge：沿 scope 父子链合并，近端 scope 覆盖远端 scope。
  注意：dsh 源码是 TypeScript 写的，我们用 Python 模仿它的机制；
  TS 语法看不懂时，去查笔记里的《附录-TS语法速查》。

2) 一条父子链
  每个 scope 有父 scope，读到的是「视角」：沿链继承。
  合并时近端 shadow 远端——同名配置，离你近的那个赢。

3) 对应笔记章节：01-scope

4) Java 对照：Spring Profile 覆盖 / 配置中心多级覆盖
  application.yml 是全局默认，application-prod.yml 覆盖同名项；
  配置中心里应用级 > 全局级。都是「近端优先」。

5) 为什么要有这层
  所有 agent 共享全局默认（模型、温度），但每个 agent 只改自己在乎的几项，
  互不干扰——不用为每个 agent 复制一份全量配置。
"""

STARTER_CODE = """\
# 任务：实现 class ScopedLayers —— 分层配置：全局层大家共享，每个 agent 自己的层可以覆盖全局
# 1. register(name, value, scope=None)：scope=None 注册到全局层，否则注册到该 scope 自己的层
# 2. merge(scope)：返回该 scope 视角的合并 dict —— 先放全局层，再用该 scope 的层覆盖同名项
# 期望输出：
# agent-A 的温度：0.1
# agent-B 的温度：0.7

class ScopedLayers:
    def __init__(self):
        self.layers = {}

    def register(self, name, value, scope=None):
        self.layers.setdefault(___, {})[name] = value  # 填：放进哪一层（提示：就是参数 scope）

    def merge(self, scope):
        merged = {}
        merged.update(self.layers.get(None, {}))   # 先放全局层
        merged.update(self.layers.get(___, {}))    # 填：再放谁的层来覆盖（提示：近端 scope）
        return merged

layers = ScopedLayers()
layers.register("模型", "deepseek-chat")
layers.register("温度", 0.7)
layers.register("温度", ___, scope="agent-A")  # 填：agent-A 自己的温度（提示：0.1）

a_view = layers.merge("agent-A")
b_view = layers.merge(___)  # 填：另一个没覆盖过的 agent（提示："agent-B"）
print(f"agent-A 的温度：{a_view['温度']}")
print(f"agent-B 的温度：{b_view['温度']}")
"""

SOLUTION = """\
class ScopedLayers:
    def __init__(self):
        self.layers = {}

    def register(self, name, value, scope=None):
        self.layers.setdefault(scope, {})[name] = value

    def merge(self, scope):
        merged = {}
        merged.update(self.layers.get(None, {}))
        merged.update(self.layers.get(scope, {}))
        return merged

layers = ScopedLayers()
layers.register("模型", "deepseek-chat")
layers.register("温度", 0.7)
layers.register("温度", 0.1, scope="agent-A")

a_view = layers.merge("agent-A")
b_view = layers.merge("agent-B")
print(f"agent-A 的温度：{a_view['温度']}")
print(f"agent-B 的温度：{b_view['温度']}")
"""

EXPECTED_OUTPUT = "agent-A 的温度：0.1\nagent-B 的温度：0.7"


def _find_class(tree: ast.AST, name: str) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _has_override(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "update"
        ):
            return True
        if isinstance(node, ast.Dict) and any(key is None for key in node.keys):
            return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "agent-A 的温度：0.1\n"
            "agent-B 的温度：0.7"
        )
    tree = ast.parse(source)
    cls = _find_class(tree, "ScopedLayers")
    if cls is None:
        return False, (
            "结果对了，但本关要求定义 class ScopedLayers（含 register / merge 方法），"
            "不能直接写 dict 打印答案"
        )
    methods = {
        item.name for item in cls.body if isinstance(item, ast.FunctionDef)
    }
    if "register" not in methods or "merge" not in methods:
        return False, "ScopedLayers 里要有 register 和 merge 两个方法——一个负责写层，一个负责算视角"
    merge_fns = [
        item for item in cls.body
        if isinstance(item, ast.FunctionDef) and item.name == "merge"
    ]
    if not any(_has_override(fn) for fn in merge_fns):
        return False, (
            "merge 里要有覆盖逻辑（dict.update 或 {**全局, **本层} 字典解包）——"
            "近端覆盖远端是这关的灵魂"
        )
    return True, "过关！全局共享 + 近端覆盖——每个 agent 都有了自己的「私人配置」。"
