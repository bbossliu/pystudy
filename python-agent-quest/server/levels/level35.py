import ast

from server.runner import RunResult

ID = 35
TITLE = "字符串方法族：拆解用户指令"

STORY = (
    "小K 收到的用户输入永远不干净：首尾带空格、字段拿逗号糊在一起。"
    "f-string 管的是输出端，输入端的拆解要靠字符串方法族——"
    "strip 削边、split 切段、join 拼回。这一关把一条脏指令拆成结构化数据。"
)

KNOWLEDGE = """\
字符串方法族——拆解与拼装文本的瑞士军刀。

1) 点题
  字符串是 agent 和用户之间的通用货币。
  f-string 负责「拼出来」，方法族负责「拆开来」。

2) 核心用法
  s.strip()         # 去首尾空白
  s.split(",")      # 按逗号切成列表
  "|".join(parts)   # 列表拼回字符串
  s.replace("a", "b") / s.startswith("查")
  s[1:3]            # 切片：取第 2、3 个字符

3) Java 对照
  strip()          ≈ Java trim() / strip()
  split(",")       ≈ Java split(",")，但返回列表不是数组
  "|".join(list)   ≈ Java String.join("|", list)
  startswith("查") ≈ Java startsWith("查")
  s[1:3]           ≈ Java substring(1, 3)

4) 坑与边界
  Python 字符串不可变（和 Java 一样）：
  所有方法都返回新串，原串纹丝不动——
  s.strip() 不写 s = s.strip() 等于白调。
  split() 不传参数按任意空白切，还自动丢空段。

5) 延伸
  对应莫烦 8.1「字符串」。
  简单拆字段用方法族就够；格式匹配（如工单号）
  要请正则出场——下一关见。
"""

STARTER_CODE = """\
# 任务：拆解用户发来的指令串
# 1. strip 去掉 raw 首尾的空白
# 2. 按 "," split 成一个列表 parts
# 3. 打印列表里的城市：城市：北京
# 4. 用 "|" 把 parts join 成一个字符串并打印
# 期望输出：
# 城市：北京
# 查天气|北京|今天

raw = "  查天气,北京,今天 "

cleaned = raw.___()       # 填：去首尾空白的方法
parts = cleaned.___(",")  # 填：切段的方法

print(f"城市：{parts[___]}")  # 填：「北京」是第几项？（从 0 开始数）

line = "|".___(parts)     # 填：把列表拼回字符串的方法
print(line)
"""

SOLUTION = """\
raw = "  查天气,北京,今天 "

cleaned = raw.strip()
parts = cleaned.split(",")

print(f"城市：{parts[1]}")

line = "|".join(parts)
print(line)
"""

EXPECTED_OUTPUT = "城市：北京\n查天气|北京|今天"


def _has_call(tree: ast.AST, *names: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in names
        for node in ast.walk(tree)
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "城市：北京\n查天气|北京|今天"
        )
    tree = ast.parse(source)
    if not _has_call(tree, "split"):
        return False, (
            "结果对了，但没看到 split——拆指令要用 "
            'cleaned.split(",") 把字符串切成列表，别直接打印答案'
        )
    if not _has_call(tree, "join", "strip"):
        return False, (
            "结果对了，但还差一步——拼接用 \"|\".join(parts)，"
            "去空白用 strip()，至少把一个用上"
        )
    return True, "过关！strip 削边、split 切段、join 拼回——输入端拆解三件套到手。"
