import ast

from server.runner import RunResult

ID = 36
TITLE = "正则表达式：一行抠出工单号"

STORY = (
    "用户消息里混着工单号，格式是 GD- 加 6 位数字，小K 要把它们全抠出来派单。"
    "手写 find 加切片？位置算到头秃还一堆边界 bug。"
    "这种「长什么样」的匹配，正则一行搞定。"
)

KNOWLEDGE = """\
正则表达式——用「模式」描述文本，引擎替你找。

1) 点题
  手写 find/切片解析格式串又脆又累。
  正则把「目标长什么样」写成模式，一行匹配。

2) 核心用法
  import re
  re.findall(r"GD-\\d{6}", text)  # 找出全部，返回列表
  re.search(r"\\d+", text)        # 只找第一个

3) Java 对照
  Java：Pattern.compile(...) 再 Matcher.find()，绕两道弯；
  Python：re 模块级直接用，不用先 compile。
  而且 Java 里 \\d 要写两反斜杠，Python 加 r 就免转义。

4) 坑与边界
  模式字符串前一定加 r（原始字符串）：
  不写 r，"\\b" 会先被 Python 当成回退符吃掉，
  模式里想要的「单词边界」就没了。
  findall 没匹配时返回空列表 []，不报错——记得判空。
  下图：正则 GD-\\d{6} 分三段各管什么。

5) 延伸
  对应莫烦 5.3「正则表达式」。
  按固定分隔符拆字段用 split 就够（上一关），
  「格式匹配」才上正则——杀鸡不用屠龙刀。
"""

STARTER_CODE = """\
# 任务：从用户消息里抠出所有工单号（格式：GD- 加 6 位数字）
# 用 re 的正则匹配一次全找出来，直接打印结果列表
# 期望输出：
# ['GD-102938', 'GD-000415']

import re

text = "用户说：工单 GD-102938 很急，另外 GD-000415 也看下，谢谢"

pattern = r"GD-\\___"             # 填：\\d 表示一个数字，{6} 表示重复 6 次
tickets = re.___(pattern, text)   # 填：找出「全部」匹配的函数
print(tickets)
"""

SOLUTION = """\
import re

text = "用户说：工单 GD-102938 很急，另外 GD-000415 也看下，谢谢"

pattern = r"GD-\\d{6}"
tickets = re.findall(pattern, text)
print(tickets)
"""

EXPECTED_OUTPUT = "['GD-102938', 'GD-000415']"

# 正则逐段含义：字面量 GD- → 数字 \d → 重复 6 次 {6}
DIAGRAM = r"""graph LR
    P["正则：GD-\d{6}"] --> L["GD-<br>字面量，原样匹配"]
    L --> D["\d<br>任意一个数字 0-9"]
    D --> S["{6}<br>前面的 \d 重复 6 次"]
"""

_RE_FUNCS = ("findall", "search", "finditer", "match")


def _has_re_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in _RE_FUNCS:
            return True
        # 兼容 from re import findall 的写法
        if isinstance(func, ast.Name) and func.id in _RE_FUNCS:
            return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望直接打印 findall 返回的列表：\n"
            "['GD-102938', 'GD-000415']"
        )
    tree = ast.parse(source)
    if not _has_re_call(tree):
        return False, (
            "结果对了，但没看到 findall/search 等匹配调用——"
            "光写 re.compile 不算数，要用 re.findall / search / "
            "finditer 真正把结果匹配出来"
        )
    return True, "过关！一个模式抠出全部工单号——正则这只手术刀你拿稳了。"
