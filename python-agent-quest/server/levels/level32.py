import ast

from server.runner import RunResult

ID = 32
TITLE = "数据处理：条件筛选与基础统计"

STORY = (
    "有用户反馈 agent 偶尔「卡」——你怀疑是长对话拖慢的。"
    "还是那份对话日志，这次把 token 超过 100 的「慢对话」单独捞出来，"
    "看看有几条、最慢的多离谱，再算算 token 总量。"
)

KNOWLEDGE = """\
布尔筛选 + 聚合统计——pandas 里的 WHERE 和聚合函数。

1) 对应莫烦章节：Pandas 3.1（基础统计）/ 4.1（运算方法）

2) 布尔筛选 = SQL 的 WHERE
  df[df["token数"] > 100]
  读作「token数 大于 100 的那些行」。
  df["token数"] > 100 先得到一列 True/False（布尔 Series），
  再套一层 df[...] 就把 True 的行挑出来——
  对应 SQL 的 WHERE token数 > 100，也像 Java Stream 的 filter。

3) 聚合方法 = SQL 的聚合函数
  筛出来的列（Series）自带 .max() .min() .sum() .mean()，
  就是 SQL 里的 MAX / MIN / SUM / AVG；数行数用 len(df)。
  Java 里得 for 循环一个个累加，pandas 一个方法搞定。

4) 链着写
  df[df["token数"] > 100]["token数"].max()
  筛选、取列、聚合一气呵成，从左读到右就是执行顺序。
"""

STARTER_CODE = """\
# 任务：还是第 31 关那份对话日志，排查「慢对话」（token > 100）
# 1. 布尔筛选出 token数 > 100 的行，打印条数：慢对话条数：{}
# 2. 打印慢对话里最大的 token：最慢的一条：{}
# 3. 打印全表 token 总和：总 token：{}
# 期望输出：
# 慢对话条数：2
# 最慢的一条：203
# 总 token：379

import pandas as pd

log = {
    "轮次": [1, 2, 3, 4],
    "角色": ["user", "assistant", "user", "assistant"],
    "token数": [12, 156, 8, 203],
}
df = pd.DataFrame(log)

slow = df[df["token数"] ___ 100]  # 填：一个比较运算符
print(f"慢对话条数：{___(slow)}")  # 填：数行数的内置函数

print(f"最慢的一条：{slow['token数'].___()}")  # 填：求最大值的方法
print(f"总 token：{df['token数'].___()}")  # 填：求总和的方法
"""

SOLUTION = """\
import pandas as pd

log = {
    "轮次": [1, 2, 3, 4],
    "角色": ["user", "assistant", "user", "assistant"],
    "token数": [12, 156, 8, 203],
}
df = pd.DataFrame(log)

slow = df[df["token数"] > 100]
print(f"慢对话条数：{len(slow)}")

print(f"最慢的一条：{slow['token数'].max()}")
print(f"总 token：{df['token数'].sum()}")
"""

EXPECTED_OUTPUT = "慢对话条数：2\n最慢的一条：203\n总 token：379"

_AGG_FUNCS = ("mean", "max", "sum")


def _has_boolean_filter(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            if any(isinstance(inner, ast.Compare) for inner in ast.walk(node.slice)):
                return True
    return False


def _agg_call_names(tree: ast.AST) -> set:
    names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _AGG_FUNCS
        ):
            names.add(node.func.attr)
    return names


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印三行：\n"
            "慢对话条数：2\n"
            "最慢的一条：203\n"
            "总 token：379"
        )
    tree = ast.parse(source)
    if not _has_boolean_filter(tree):
        return False, (
            "结果对了，但没看到布尔筛选——要用 df[df[\"token数\"] > 100] "
            "这种写法，像 SQL 的 WHERE，别用循环或推导式一个个挑"
        )
    if len(_agg_call_names(tree)) < 2:
        return False, (
            "结果对了，但聚合方法没用够——.max() / .sum() / .mean() "
            "这类 Series 聚合至少用两个，别自己手写逻辑算"
        )
    return True, "过关！布尔筛选像 WHERE，聚合方法像 SQL 函数——慢对话无处遁形。"
