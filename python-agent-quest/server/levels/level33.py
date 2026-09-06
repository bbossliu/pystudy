import ast

from server.runner import RunResult

ID = 33
TITLE = "数据处理：缺失值与文字处理"

STORY = (
    "从线上导出的真实日志可没这么干净：token 数有空缺，"
    "角色名大小写乱七八糟——「User」「USER」其实是同一个人。"
    "数据分析的第一步，永远是先把数据洗干净。"
)

KNOWLEDGE = """\
数据清洗——真实数据永远是脏的。

1) 对应莫烦章节：Pandas 4.2（文字处理）/ 4.3（异常数据处理）

2) 缺失值 NaN
  数据里的 None 进了 DataFrame 就变成 NaN（Not a Number）。
  两条路：fillna(值) 填上，或 dropna() 整行丢掉——
  像 Java 的 Optional.orElse(...)，但一次处理整列。
  常用均值填充：df["token数"].fillna(df["token数"].mean())，
  既不丢数据，也不拉偏统计。

3) .str 访问器——整列字符串操作
  df["角色"].str.lower() 把整列统一转小写，
  相当于 Java 的 list.stream().map(String::toLowerCase)，
  但不用写循环——大小写混乱的 "User"/"USER" 一次归一。

4) 先洗后算
  清洗完再统计，结果才可信——
  拿脏数据直接算，结论全是错的。
"""

STARTER_CODE = """\
# 任务：清洗一份真实的脏日志
# 1. 「角色」列统一转小写（提示：.str.lower()）
# 2. 「token数」列的缺失值用该列均值填充（提示：fillna）
# 3. 打印清洗后 user 的条数：user 条数：{}
# 4. 打印填充后的 token 总和（转 int）：清洗后总 token：{}
# 期望输出：
# user 条数：2
# 清洗后总 token：567

import pandas as pd

log = {
    "轮次": [1, 2, 3, 4, 5, 6],
    "角色": ["User", "assistant", "USER", "Assistant", "tool", "ASSISTANT"],
    "token数": [12, None, 8, None, 156, 202],
}
df = pd.DataFrame(log)

df["角色"] = df["角色"].___.lower()  # 填：字符串访问器（提示：str）

mean_token = df["token数"].mean()  # 均值会自动跳过缺失值
df["token数"] = df["token数"].___(mean_token)  # 填：填充缺失值的方法

print(f"user 条数：{len(df[df['角色'] == 'user'])}")
print(f"清洗后总 token：{int(df['token数'].sum())}")
"""

SOLUTION = """\
import pandas as pd

log = {
    "轮次": [1, 2, 3, 4, 5, 6],
    "角色": ["User", "assistant", "USER", "Assistant", "tool", "ASSISTANT"],
    "token数": [12, None, 8, None, 156, 202],
}
df = pd.DataFrame(log)

df["角色"] = df["角色"].str.lower()

mean_token = df["token数"].mean()
df["token数"] = df["token数"].fillna(mean_token)

print(f"user 条数：{len(df[df['角色'] == 'user'])}")
print(f"清洗后总 token：{int(df['token数'].sum())}")
"""

EXPECTED_OUTPUT = "user 条数：2\n清洗后总 token：567"


def _has_attr(tree: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.Attribute) and node.attr == name
        for node in ast.walk(tree)
    )


def _has_na_call(tree: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("fillna", "dropna")
        for node in ast.walk(tree)
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "user 条数：2\n"
            "清洗后总 token：567"
        )
    tree = ast.parse(source)
    if not _has_attr(tree, "str"):
        return False, (
            "结果对了，但没看到 .str——整列字符串统一处理要用 "
            'df["角色"].str.lower()，别写循环一个个 lower'
        )
    if not _has_na_call(tree):
        return False, (
            "结果对了，但没看到 fillna/dropna——缺失值交给 pandas 处理，"
            "比如 df[\"token数\"].fillna(均值)，别手写 if None 判断"
        )
    return True, "过关！fillna 补缺、str 归一——数据洗干净，结论才站得住。"
