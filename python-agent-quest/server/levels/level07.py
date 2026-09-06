import ast

from server.runner import RunResult

ID = 7
TITLE = "异常处理：工具调用会失败"

STORY = (
    "小K 开始调用外部工具了，可外面的世界不靠谱：网络会抖、返回格式会乱。"
    "不能一个异常就让整个 agent 崩掉——给它装上容错能力。"
)

KNOWLEDGE = """\
try/except 对比 Java 的 try/catch——不用声明 throws：

```plaintext
  Java:   try { ... } catch (NumberFormatException e) { ... } finally { ... }
  Python: try:
              ...
          except ValueError:
              ...
          finally:
              ...
```

要点：
  - 不用在方法签名上声明 throws，任何函数都可能抛异常
  - except ValueError 只捕获指定异常，别裸写 except（会把真正的 bug 也吞掉）
  - finally 和 Java 一样，无论成败都执行
  - Python 风格是 "ask for forgiveness"：先做了再说，出错再补救，而不是先层层检查
"""

STARTER_CODE = """\
# 任务：raw_results 模拟工具返回的原始结果，用 for + try/except 逐项转成 int
# 转换成功 → 打印：结果：42
# 转换失败（ValueError）→ 打印：跳过无效结果：abc
# 期望输出：
# 结果：42
# 跳过无效结果：abc
# 结果：7

raw_results = ["42", "abc", "7"]

for raw in raw_results:
    ___  # 提示：try
        number = int(raw)
        print(f"结果：{number}")
    ___  # 提示：except ValueError:
        print(f"跳过无效结果：{raw}")
"""

SOLUTION = """\
raw_results = ["42", "abc", "7"]

for raw in raw_results:
    try:
        number = int(raw)
        print(f"结果：{number}")
    except ValueError:
        print(f"跳过无效结果：{raw}")
"""

EXPECTED_OUTPUT = "结果：42\n跳过无效结果：abc\n结果：7"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印三行：\n"
            "结果：42\n跳过无效结果：abc\n结果：7"
        )
    tree = ast.parse(source)
    try_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]
    if not try_nodes:
        return False, "结果对了，但本关要求用 try/except 容错，不能用 if 预判或直接打印答案"
    def catches_value_error(handler: ast.ExceptHandler) -> bool:
        t = handler.type
        if isinstance(t, ast.Name) and t.id == "ValueError":
            return True
        if isinstance(t, ast.Tuple):  # except (ValueError, TypeError): 这种写法
            return any(isinstance(e, ast.Name) and e.id == "ValueError" for e in t.elts)
        return False

    catches = any(catches_value_error(handler) for node in try_nodes for handler in node.handlers)
    if not catches:
        return False, "except 要捕获指定异常 ValueError，别裸写 except"
    return True, "过关！小K 遇到工具故障不会崩了。"
