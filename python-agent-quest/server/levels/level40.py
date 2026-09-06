import ast

from server.runner import RunResult

ID = 40
TITLE = "用 pytest 写单元测试"

STORY = (
    "小K 的代码越写越多，改一处怕坏三处。"
    "Java 人懂 JUnit，Python 这边是 pytest——断言更裸、参数化更爽。"
    "闯关环境是单文件，先手写一个迷你执行器，把测试收集的机制摸清楚。"
)

KNOWLEDGE = """\
pytest——Python 的单元测试框架，断言更裸。

1) 点题
  改一处怕坏三处？让测试函数帮你守着。
  Java 用 JUnit，Python 这边 pytest 是主流。

2) 核心用法
  def add(a, b):
      return a + b
  def test_add():                  # test_ 开头
      assert add(1, 2) == 3        # 断言直接写

3) Java 对照
  assert a == b            ≈ JUnit assertEquals
  @pytest.mark.parametrize ≈ @ParameterizedTest
  with pytest.raises(Err)  ≈ assertThrows
  真实项目跑 pytest tests/，框架自动收集执行。

4) 坑与边界
  文件名和函数名都要 test_ 开头，
  否则 pytest 根本收不到你的用例。
  assert 失败抛 AssertionError，框架接住记 FAIL。
  本关用迷你 runner 演示同样的收集机制：
  遍历 test_ 前缀函数、逐个执行、报告结果。

5) 延伸
  对应莫烦 6.2「单元测试」。
  一次性脚本不必配测试；要长期维护的逻辑，
  测试是最便宜的返工保险。
"""

STARTER_CODE = """\
# 任务：给 add 函数写单元测试（本关一个文件里搞定三件事）
# 1. 实现被测函数 add(a, b)：返回两数之和
# 2. 实现测试函数 test_add()：至少 3 条 assert（正数 / 负数 / 零）
# 3. 迷你测试执行器已内置，会自动执行所有 test_ 开头的函数
# 期望输出：
# test_add 通过

def add(a, b):
    ___   # 填：返回 a + b

def test_add():
    assert add(1, 2) == ___    # 填：期望结果
    assert add(-1, 1) == ___
    assert add(0, 0) == ___

# ---- 迷你测试执行器（真实项目直接用 pytest 命令代替）----
for name, fn in list(globals().items()):
    if name.startswith("test_") and callable(fn):
        fn()
        print(f"{name} 通过")
"""

SOLUTION = """\
def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

for name, fn in list(globals().items()):
    if name.startswith("test_") and callable(fn):
        fn()
        print(f"{name} 通过")
"""

EXPECTED_OUTPUT = "test_add 通过"

_MIN_ASSERTS = 3


def _test_func_assert_count(tree: ast.AST) -> int:
    best = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            count = sum(1 for inner in ast.walk(node) if isinstance(inner, ast.Assert))
            best = max(best, count)
    return best


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望迷你 runner 打印一行：\n"
            "test_add 通过"
        )
    tree = ast.parse(source)
    has_test_func = any(
        isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        for node in ast.walk(tree)
    )
    if not has_test_func:
        return False, (
            "结果对了，但没看到 test_ 开头的测试函数——"
            "pytest 靠这个名字收集用例，函数名必须是 test_add"
        )
    if _test_func_assert_count(tree) < _MIN_ASSERTS:
        return False, (
            "结果对了，但 test_add 里 assert 不到 3 条——"
            "正常、负数、零各断一条，测试才算真测了"
        )
    return True, "过关！test_ 开头加裸 assert——pytest 的收集机制你摸透了。"
