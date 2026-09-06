import ast

from server.runner import RunResult

ID = 29
TITLE = "数据处理：ndarray 与向量化"

STORY = (
    "你的 agent 上线一周了，日志里攒了一批响应耗时数据。"
    "产品来问：平均多快？最慢多慢？要是网络延迟统一修正 100ms 呢？"
    "别再用 for 循环一个个加了——这一关用 numpy 的向量化，一次搞定整批数据。"
)

KNOWLEDGE = """\
ndarray——一个数组，整体运算。

1) 对应莫烦章节：Numpy 1.3（和 List 的差别）/ 2.3（基础运算）

2) np.array vs Java 的 int[]
  看起来像 Java 的数组，但运算符的含义完全不同：
  Java 里 arr[i] + 100 要手写循环，Stream 也只是把循环包装起来；
  numpy 里 arr + 100 是对整个数组的「向量化」操作——一个表达式，全员生效。
  arr.mean()、arr.max() 这类聚合也是一口气算完，不用自己累加。

3) 向量化为什么快？
  numpy 底层是一块连续的 C 内存，运算在 C 层跑完，
  没有 Python 解释器逐条执行的开销。数据越多，和 for 循环的差距越大。

4) 用起来的两步
  import numpy as np（约定俗成的别名，就像 Java 的 import 习惯）
  arr = np.array(你的list)——把 Python list 转成 ndarray，之后就能向量化了。
"""

STARTER_CODE = """\
# 任务：分析 agent 一周的响应耗时（毫秒），用 numpy 向量化完成
# 1. 把 latencies 转成 ndarray（提示：np.array(...)）
# 2. 打印均值，格式：均值：{:.1f}（提示：数组.mean()）
# 3. 全部耗时 +100 做网络修正（提示：数组 + 100 就是全员加，不用循环），
#    打印修正后的最大值，格式：修正后最大值：{}
# 期望输出：
# 均值：347.1
# 修正后最大值：1600

import numpy as np

latencies = [120, 85, 340, 90, 1500, 200, 95]

arr = ___(latencies)  # 填：转成 ndarray
print(f"均值：{arr.___():.1f}")  # 填：求均值的方法

fixed = arr + ___  # 填：网络修正的毫秒数
print(f"修正后最大值：{fixed.___()}")  # 填：求最大值的方法
"""

SOLUTION = """\
import numpy as np

latencies = [120, 85, 340, 90, 1500, 200, 95]

arr = np.array(latencies)
print(f"均值：{arr.mean():.1f}")

fixed = arr + 100
print(f"修正后最大值：{fixed.max()}")
"""

EXPECTED_OUTPUT = "均值：347.1\n修正后最大值：1600"


def _has_np_array_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "array"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in ("np", "numpy")
        ):
            return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "均值：347.1\n"
            "修正后最大值：1600"
        )
    tree = ast.parse(source)
    if not _has_np_array_call(tree):
        return False, (
            "结果对了，但本关要求用 np.array() 把列表转成 ndarray——"
            "向量化是 numpy 的基本功，不能用纯 Python 绕过去"
        )
    if any(isinstance(node, ast.For) for node in ast.walk(tree)):
        return False, (
            "结果对了，但代码里有 for 循环——numpy 的加法和聚合都是整个数组一起算的，"
            "试试 arr + 100 和 arr.max()"
        )
    return True, "过关！一个表达式搞定整批数据——这就是向量化，for 循环可以退休了。"
