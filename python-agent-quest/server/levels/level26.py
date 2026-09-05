import ast

from server.runner import RunResult

ID = 26
TITLE = "dsh 核心六包：system-prompt——段装注册表"

STORY = (
    "第 16 关的 prompt 拼装是手写列表，顺序全靠自己摆——"
    "dsh 把它升级成了注册表：每个片段带排序权重，"
    "scoped 片段能覆盖同名全局片段，还能声明「本段独占全文」。"
    "这一关先搭注册表的核心：带权重的段装拼接。"
)

KNOWLEDGE = """\
段装注册表——prompt 不是拼字符串，是装配。

1) 源码位置
  packages/core/system-prompt/src/index.ts:518 的 assemble()：
  合并（scoped 覆盖同名全局片段）→ 按权重排序 → waterfall 逐段求值
  → 若有片段声明 complete，则独占全文。
  本关先实现核心两步：注册 + 按权重排序拼接。
  注意：dsh 源码是 TypeScript 写的，我们用 Python 模仿它的机制；
  TS 语法看不懂时，去查笔记里的《附录-TS语法速查》。

2) 为什么是注册表而不是列表
  手写列表的问题：顺序写死在一处，谁想插一段都得改同一份代码。
  注册表让片段各自声明「我是谁、排第几」，装配时统一排序——
  加片段 = 注册，不用动别人的代码。

3) 对应笔记：整体架构 ② 节（ctx.systemPrompt）

4) Java 对照：Spring 的 @Order 注解 + Bean 覆盖
  @Order 决定 Bean 注入列表里的先后；同名 Bean 后注册覆盖先注册。
  dsh 的片段权重和 scoped 覆盖就是同款思路。

5) 排序稳定性
  order 从小到大排；同权重时按注册顺序来（sorted 是稳定排序）。
  所以权重设计要留间隔（10、20、30……），方便以后插队。
"""

STARTER_CODE = """\
# 任务：实现 class PromptAssembler —— 带排序权重的 prompt 段装注册表
# 1. section(name, text, order)：注册一个片段（已写好）
# 2. assemble()：按 order 从小到大排序，用 "\\n\\n" 拼接各段 text 返回
# 期望输出（注意："风格" 权重最小，排最前）：
# 回答要简短。
#
# 你是小K。
#
# 可用工具：search

class PromptAssembler:
    def __init__(self):
        self.sections = []

    def section(self, name, text, order):
        self.sections.append({"name": name, "text": text, "order": order})

    def assemble(self):
        ordered = sorted(self.sections, key=lambda s: s[___])  # 填：按哪个字段排序（提示："order"）
        return "\\n\\n".join(s[___] for s in ordered)  # 填：拼接每段的哪个字段（提示："text"）

assembler = PromptAssembler()
assembler.section("身份", "你是小K。", 1)
assembler.section("工具", "可用工具：search", 2)
assembler.section("风格", "回答要简短。", ___)  # 填：让它排最前的权重（提示：0）
print(assembler.___())  # 填：调用哪个方法拿到拼好的 prompt（提示：assemble）
"""

SOLUTION = """\
class PromptAssembler:
    def __init__(self):
        self.sections = []

    def section(self, name, text, order):
        self.sections.append({"name": name, "text": text, "order": order})

    def assemble(self):
        ordered = sorted(self.sections, key=lambda s: s["order"])
        return "\\n\\n".join(s["text"] for s in ordered)

assembler = PromptAssembler()
assembler.section("身份", "你是小K。", 1)
assembler.section("工具", "可用工具：search", 2)
assembler.section("风格", "回答要简短。", 0)
print(assembler.assemble())
"""

EXPECTED_OUTPUT = "回答要简短。\n\n你是小K。\n\n可用工具：search"


def _find_assemble(tree: ast.AST) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "PromptAssembler":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "assemble":
                    return item
    return None


def _has_sort_call(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        # sorted(...)：func 是 Name
        if isinstance(node.func, ast.Name) and node.func.id == "sorted":
            return True
        # xxx.sort()：func 是属性 sort
        if isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
            return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望按权重从小到大拼成三段（风格 → 身份 → 工具），"
            "段与段之间空一行：\n"
            "回答要简短。\n\n你是小K。\n\n可用工具：search"
        )
    tree = ast.parse(source)
    assemble = _find_assemble(tree)
    if assemble is None:
        return False, (
            "结果对了，但本关要求定义 class PromptAssembler 并实现 assemble 方法，"
            "不能直接打印答案"
        )
    if not _has_sort_call(assemble):
        return False, (
            "assemble 里要真的排序（sorted 或 .sort()）——"
            "注册表的精髓是片段自带权重、装配时统一排，不是靠注册顺序碰巧排对"
        )
    return True, (
        "过关！片段带权重、装配时统一排序——"
        "以后加一段 prompt 只需注册，不用动别人的代码。"
    )
