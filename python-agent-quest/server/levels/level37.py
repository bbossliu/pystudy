import ast

from server.runner import RunResult

ID = 37
TITLE = "浅拷贝与深拷贝：备份别连累原件"

STORY = (
    "小K 把对话历史「复制」了一份做备份，结果改了备份、原件也跟着变了——"
    "Java 人一眼就懂这是引用。但 Python 里 =、浅拷贝、深拷贝是三层不同的语义，"
    "嵌套列表上尤其阴。这一关把它们掰开看清楚。"
)

KNOWLEDGE = """\
浅拷贝 vs 深拷贝——复制嵌套对象的三层语义。

1) 点题
  Python 的「复制」分三层：贴标签、浅拷贝、深拷贝。
  改了副本、原件跟着变，多半是用错了层。

2) 核心用法
  b = a                 # 贴新标签，还是同一对象
  c = a.copy()          # 浅拷贝：只复制外层
  d = copy.deepcopy(a)  # 深拷贝：里里外外全复制

3) Java 对照
  b = a   ≈ Java 引用赋值（List b = a），同一个对象
  浅拷贝  ≈ Java clone() / 复制构造——只复制第一层
  深拷贝  ≈ 序列化再反序列化，或手写层层 clone

4) 坑与边界
  嵌套列表浅拷贝，内层子列表仍然共享：
  改 c[0][0]，a[0][0] 跟着变！
  只有 deepcopy 才能让副本彻底独立。
  下图：① b = a 两个标签指同一对象；
  ② 浅拷贝外层是新对象、内层仍共享。

5) 延伸
  对应莫烦 8.3「复制」。
  数字、字符串不可变，共享也不怕；
  嵌套列表/字典要做备份时，才请 deepcopy 出场。
"""

STARTER_CODE = """\
# 任务：备份对话历史（嵌套列表），改备份绝不能动原件
# 1. 用 copy 模块把 a 复制出 b（注意：= 和浅拷贝都过不了关！）
# 2. 把 b[0][0] 改成 99
# 3. 分别打印 a[0][0] 和 b[0][0]，验证原件没被动过
# 期望输出：
# 原件：1
# 副本：99

import copy

a = [[1, 2], [3, 4]]

b = copy.___(a)  # 填：连内层子列表也一起复制的方法（提示：deepcopy）

b[0][0] = 99

print(f"原件：{a[0][0]}")
print(f"副本：{b[0][0]}")
"""

SOLUTION = """\
import copy

a = [[1, 2], [3, 4]]

b = copy.deepcopy(a)

b[0][0] = 99

print(f"原件：{a[0][0]}")
print(f"副本：{b[0][0]}")
"""

EXPECTED_OUTPUT = "原件：1\n副本：99"

# ① b = a：两个标签指向同一列表对象；② 浅拷贝：外层新对象、内层仍共享；③ 深拷贝：层层独立
DIAGRAM = """\
graph LR
    subgraph S1["① b = a：贴新标签，同一对象"]
        direction LR
        A["a"] --> OBJ["外层列表对象"]
        B["b"] --> OBJ
    end
    subgraph S2["② c = a.copy()：浅拷贝"]
        direction LR
        A2["a"] --> OLD["原外层列表"]
        C2["c"] --> NEW["新外层列表<br>（新对象）"]
        OLD --> INNER["子列表 [1, 2]<br>（内层仍共享）"]
        NEW --> INNER
    end
    subgraph S3["③ d = deepcopy(a)：深拷贝"]
        direction LR
        A3["a"] --> OLD2["原外层列表"]
        D3["d"] --> NEW2["新外层列表"]
        OLD2 --> OI["原子列表 [1, 2]"]
        NEW2 --> NI["新子列表 [1, 2]<br>（内层也复制了）"]
    end
"""


def _has_deepcopy_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "deepcopy":
            return True
        # 兼容 from copy import deepcopy 的写法
        if isinstance(func, ast.Name) and func.id == "deepcopy":
            return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行（原件没被动过才算备份成功）：\n"
            "原件：1\n副本：99"
        )
    tree = ast.parse(source)
    if not _has_deepcopy_call(tree):
        return False, (
            "结果对了，但没看到 deepcopy——b = a 只是贴标签，"
            "a.copy() / a[:] 只复制外层、内层子列表照样共享。"
            "嵌套列表的备份必须用 copy.deepcopy(a)"
        )
    return True, "过关！deepcopy 层层复制，改副本原件纹丝不动——备份这才算真备份。"
