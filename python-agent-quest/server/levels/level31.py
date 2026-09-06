import ast

from server.runner import RunResult

ID = 31
TITLE = "数据处理：DataFrame 与数据选取"

STORY = (
    "数组只能装数字，可你的 agent 攒下的是对话日志——"
    "每行一条消息，每列一个字段：第几轮、谁说的、花了多少 token。"
    "这就是一张表，一张表就该交给 pandas。"
)

KNOWLEDGE = """\
DataFrame——带表头的表，行列都有名字。

1) 对应莫烦章节：Pandas 1.3（和 Numpy 差别）/ 2.2（数据是什么）/ 2.3（选取数据）

2) DataFrame vs Java 的 List<Map<String, Object>>
  Java 里表示一张表，要么 List<Map<String, Object>>（类型地狱，
  取个值全是强转），要么连数据库查 SQL；
  pandas 的 DataFrame 就是内存里的一张 SQL 表——
  列有名字、行有下标，dict 直接转：pd.DataFrame({"列名": [值, ...]})。
  真实项目里更常用 pd.read_csv(...) 从文件读，这里数据内联构造。

3) 两种取法：iloc 和 loc
  iloc 按位置取：df.iloc[0] 就是第 1 行，像数组下标；
  loc 按标签/条件取：df.loc[df["角色"] == "assistant", "token数"]
  读作「角色列等于 assistant 的那些行，只要 token数 列」——
  相当于 SQL 的 SELECT token数 FROM 表 WHERE 角色='assistant'。

4) 取出来接着算
  取出来的列（Series）和 numpy 数组一样有 .mean() 这类聚合方法，
  上一关的功夫直接平移过来。
"""

STARTER_CODE = """\
# 任务：分析 agent 的对话日志，用 pandas 选取数据
# 1. 用 pd.DataFrame(...) 把 dict 转成 DataFrame
# 2. 用 iloc 取第 1 行（位置 0）的「角色」，格式：第一条消息来自：{}
# 3. 用 loc 按条件取「角色」列等于 "assistant" 的行的「token数」列，
#    打印均值，格式：assistant 平均 token：{:.1f}
# 期望输出：
# 第一条消息来自：user
# assistant 平均 token：179.5

import pandas as pd

log = {
    "轮次": [1, 2, 3, 4],
    "角色": ["user", "assistant", "user", "assistant"],
    "token数": [12, 156, 8, 203],
}

df = ___.DataFrame(log)  # 填：用 pandas 构造 DataFrame（提示：别名 pd）

first_role = df.___[0]["角色"]  # 填：按位置取行的属性（提示：iloc）
print(f"第一条消息来自：{first_role}")

assistant_tokens = df.___[df["角色"] == "assistant", "token数"]  # 填：按条件取的属性
print(f"assistant 平均 token：{assistant_tokens.mean():.1f}")
"""

SOLUTION = """\
import pandas as pd

log = {
    "轮次": [1, 2, 3, 4],
    "角色": ["user", "assistant", "user", "assistant"],
    "token数": [12, 156, 8, 203],
}

df = pd.DataFrame(log)

first_role = df.iloc[0]["角色"]
print(f"第一条消息来自：{first_role}")

assistant_tokens = df.loc[df["角色"] == "assistant", "token数"]
print(f"assistant 平均 token：{assistant_tokens.mean():.1f}")
"""

EXPECTED_OUTPUT = "第一条消息来自：user\nassistant 平均 token：179.5"


def _has_pd_dataframe_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "DataFrame"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in ("pd", "pandas")
        ):
            return True
    return False


def _has_attr(tree: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.Attribute) and node.attr == name
        for node in ast.walk(tree)
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "第一条消息来自：user\n"
            "assistant 平均 token：179.5"
        )
    tree = ast.parse(source)
    if not _has_pd_dataframe_call(tree):
        return False, (
            "结果对了，但本关要求用 pd.DataFrame() 把日志构造成 DataFrame——"
            "表格数据交给 pandas，不能用纯 Python 字典列表绕过去"
        )
    if not _has_attr(tree, "iloc"):
        return False, (
            "结果对了，但没看到 iloc——按位置取行要用 df.iloc[0]，"
            "i 是 index（位置）的意思"
        )
    if not _has_attr(tree, "loc"):
        return False, (
            "结果对了，但没看到 loc——按条件筛选要用 "
            'df.loc[df["角色"] == "assistant", "token数"]，像写 SQL 的 WHERE'
        )
    return True, "过关！表格在手，iloc 按位置、loc 按条件——查数据像写 SQL 一样自然。"
