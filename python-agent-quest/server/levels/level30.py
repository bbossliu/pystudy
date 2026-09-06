import ast

from server.runner import RunResult

ID = 30
TITLE = "数据处理：维度、索引切片与 reshape"

STORY = (
    "一条线的耗时数据看不出规律——按「天 × 时段」重新组织才有意义。"
    "这一关把一维数据 reshape 成二维矩阵，然后按行按列切着看："
    "第 2 天发生了什么？每天的 0 时段又是什么样？"
)

KNOWLEDGE = """\
维度与切片——换种看法，数据不变。

1) 对应莫烦章节：Numpy 2.1（维度）/ 2.2（数据选择）/ 2.4（改变数据形态）

2) shape vs Java 二维数组
  Java 里你写 int[3][4]，内存布局其实是一维数组套一维数组；
  numpy 的二维数组是真的一块连续内存，shape 属性告诉你它是 (3, 4)。
  reshape(3, 4) 不复制、不修改数据，只是换一种「看法」——
  同 12 个数，排成 3 行 4 列。

3) 切片 vs Java 手取下标
  Java 取第 2 行：int[] row = matrix[1]，取一列还得写循环；
  numpy 里 arr[1, :] 是第 2 行，arr[:, 0] 是第 1 列——
  逗号分隔维度，冒号表示「这一维全要」。

4) 下标从 0 开始
  「第 2 天」是 arr[1, :]，「时段 0」是 arr[:, 0]。
  和 Java 一样从 0 数起，别数错了。
"""

STARTER_CODE = """\
# 任务：12 个数据是 agent 3 天 × 每天 4 个时段的调用次数，用 numpy 切着看
# 1. 把 data reshape 成 3 行 4 列，打印 shape，格式：形状：{}
# 2. 取第 2 行（第 2 天）直接 print，格式：第 2 天：{}
# 3. 取第 1 列（每天的时段 0）直接 print，格式：时段 0：{}
# 提示：逗号分隔维度，冒号 : 表示这一维全要
# 期望输出：
# 形状：(3, 4)
# 第 2 天：[4 5 6 7]
# 时段 0：[0 4 8]

import numpy as np

data = np.arange(12)  # 0 到 11，一维

m = data.___(3, 4)  # 填：改成 3 行 4 列的方法
print(f"形状：{m.___}")  # 填：查看形状的属性（不是方法，没括号）

print(f"第 2 天：{m[___, ___]}")  # 填：第 2 行 = 下标 1 的那一行，列全要
print(f"时段 0：{m[___, ___]}")  # 填：行全要，只要下标 0 的那一列
"""

SOLUTION = """\
import numpy as np

data = np.arange(12)

m = data.reshape(3, 4)
print(f"形状：{m.shape}")

print(f"第 2 天：{m[1, :]}")
print(f"时段 0：{m[:, 0]}")
"""

EXPECTED_OUTPUT = "形状：(3, 4)\n第 2 天：[4 5 6 7]\n时段 0：[0 4 8]"


def _has_reshape_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "reshape"
        ):
            return True
    return False


def _has_slice_subscript(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Slice):
                return True
            if isinstance(node.slice, ast.Tuple) and any(
                isinstance(elt, ast.Slice) for elt in node.slice.elts
            ):
                return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印三行：\n"
            "形状：(3, 4)\n"
            "第 2 天：[4 5 6 7]\n"
            "时段 0：[0 4 8]"
        )
    tree = ast.parse(source)
    if not _has_reshape_call(tree):
        return False, (
            "结果对了，但本关要求用 reshape() 把一维数据变成 3 行 4 列——"
            "reshape 是这关的主角，不能手写答案"
        )
    if not _has_slice_subscript(tree):
        return False, (
            "结果对了，但没看到切片——取行取列要用 arr[1, :]、arr[:, 0] 这种切片语法，"
            "冒号表示这一维全要"
        )
    return True, "过关！reshape 换看法，切片随便切——二维数据任你摆布了。"
