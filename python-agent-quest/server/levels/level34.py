import ast

from server.runner import RunResult

ID = 34
TITLE = "数据处理：groupby 聚合分析"

STORY = (
    "周一早会要交周报了：user、assistant、tool 三种角色各聊了多少、"
    "谁最烧 token？不用写循环分堆，一条 groupby 出一张汇总表，一目了然。"
)

KNOWLEDGE = """\
groupby——分组聚合，一张表看清全局。

1) 对应莫烦章节：Pandas 5.2（Groupby）/ 5.1（Concat 和 Merge）

2) groupby = SQL 的 GROUP BY
  df.groupby("角色")["token数"].mean()
  就是 SELECT 角色, AVG(token数) FROM 表 GROUP BY 角色；
  Java 里是 Collectors.groupingBy(角色, averagingInt(token))——
  概念一模一样，pandas 写起来最短。

3) split-apply-combine 三步
  split：按「角色」把表拆成几堆；
  apply：每堆各算各的（mean / sum / max）；
  combine：结果拼回一张以角色为索引的表。
  所有的分组统计都是这个套路。

4) 找「最」
  groupby(...).sum() 之后用 .idxmax() 拿到总和最大的组名——
  max() 只给你数值，idxmax() 告诉你「是谁」。
"""

STARTER_CODE = """\
# 任务：一周对话日志（7 条），按角色做周报汇总
# 1. 按「角色」分组，打印每个角色的平均 token（直接 print 分组聚合结果）
# 2. 按「角色」求 token 总和，用 idxmax() 找出消耗最多的角色：消耗最多：{}
# 期望输出（pandas 打印格式固定，照抄即可）：
# 角色
# assistant    190.0
# tool          52.5
# user          12.5
# Name: token数, dtype: float64
# 消耗最多：assistant

import pandas as pd

log = {
    "轮次": [1, 2, 3, 4, 5, 6, 7],
    "角色": ["user", "assistant", "tool", "user", "assistant", "tool", "assistant"],
    "token数": [15, 180, 45, 10, 220, 60, 170],
}
df = pd.DataFrame(log)

avg_tokens = df.___("角色")["token数"].mean()  # 填：分组方法（提示：groupby）
print(avg_tokens)

total_tokens = df.___("角色")["token数"].sum()  # 填：还是分组方法
print(f"消耗最多：{total_tokens.idxmax()}")
"""

SOLUTION = """\
import pandas as pd

log = {
    "轮次": [1, 2, 3, 4, 5, 6, 7],
    "角色": ["user", "assistant", "tool", "user", "assistant", "tool", "assistant"],
    "token数": [15, 180, 45, 10, 220, 60, 170],
}
df = pd.DataFrame(log)

avg_tokens = df.groupby("角色")["token数"].mean()
print(avg_tokens)

total_tokens = df.groupby("角色")["token数"].sum()
print(f"消耗最多：{total_tokens.idxmax()}")
"""

EXPECTED_OUTPUT = (
    "角色\n"
    "assistant    190.0\n"
    "tool          52.5\n"
    "user          12.5\n"
    "Name: token数, dtype: float64\n"
    "消耗最多：assistant"
)

_AGG_FUNCS = ("mean", "sum", "max", "agg")


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
            "输出不对哦，期望打印六行（pandas 的打印格式一个空格都不能差）：\n"
            "角色\n"
            "assistant    190.0\n"
            "tool          52.5\n"
            "user          12.5\n"
            "Name: token数, dtype: float64\n"
            "消耗最多：assistant"
        )
    tree = ast.parse(source)
    if not _has_call(tree, "groupby"):
        return False, (
            "结果对了，但没看到 groupby——按角色汇总要用 "
            'df.groupby("角色")，像 SQL 的 GROUP BY，别手写循环分堆'
        )
    if not _has_call(tree, *_AGG_FUNCS):
        return False, (
            "结果对了，但 groupby 之后要接聚合——"
            ".mean() / .sum() / .max() 至少用一个，split 之后还得 apply"
        )
    return True, "过关！groupby 一出手，周报一张表——split-apply-combine 你已经会了。"
