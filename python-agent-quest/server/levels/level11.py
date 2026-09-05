import ast
import os

from server.runner import RunResult

ID = 11
TITLE = "模块与包：拆分项目"

STORY = (
    "所有代码还挤在一个文件里，已经开始难找了。真实项目要拆模块——"
    "agent 项目通常分成 tools.py、agent.py、main.py。"
    "这一关用「代码里写出 toolkit.py 再 import」的方式演示模块机制；"
    "真实项目里你是直接在编辑器新建文件，不用这么绕。"
)

KNOWLEDGE = """\
import 对比 Java 的 import + package：

1) 每个 .py 文件就是一个模块
  Java 要 package 声明 + public class，文件名还得和类名一致；
  Python 里 toolkit.py 天然就是名为 toolkit 的模块，不用显式导出任何东西。

2) import 的两种写法
  import toolkit            → 用 toolkit.greet(...) 访问（带模块名前缀）
  from toolkit import greet → 直接写 greet(...)（类似 Java 的 static import）

3) 导入即执行
  import 一个模块时它的顶层代码会跑一遍（整个文件只执行一次，之后走缓存）。
  所以「只想在直接运行时才执行」的代码要包在：
      if __name__ == "__main__":
  里——__name__ 在直接运行时是 "__main__"，被 import 时是模块名。
  对比 Java：相当于把 main 方法的入口判断写在了文件级别。

4) 包（package）
  一个放了 __init__.py 的目录就是包，类似 Java 的 package；
  import 时 Python 会在当前目录和 sys.path 里查找模块。
"""

STARTER_CODE = """\
# 任务：先用代码把工具函数写进 toolkit.py 文件，再 import 它并调用
# （这是为了演示模块机制——真实项目里你直接新建 toolkit.py 文件即可）
# 期望输出：你好，小K

with open("toolkit.py", "w", encoding="utf-8") as f:
    f.write(___)  # 写入一个函数定义：def greet(name): 返回 f"你好，{name}"

___  # 填：import toolkit

print(toolkit.greet("小K"))
"""

SOLUTION = """\
with open("toolkit.py", "w", encoding="utf-8") as f:
    f.write('def greet(name):\\n    return f"你好，{name}"\\n')

import toolkit

print(toolkit.greet("小K"))
"""

EXPECTED_OUTPUT = "你好，小K"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, "输出不对哦，期望打印：你好，小K"
    tree = ast.parse(source)
    imports_toolkit = any(
        (isinstance(node, ast.Import) and any(alias.name == "toolkit" for alias in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "toolkit")
        for node in ast.walk(tree)
    )
    if not imports_toolkit:
        return False, "输出对了，但本关要用 import 导入 toolkit 模块，不能在同一个文件里一把梭"
    toolkit_path = os.path.join(result.workdir, "toolkit.py")
    if not os.path.exists(toolkit_path):
        return False, "输出对了，但运行目录里没有 toolkit.py——要先用代码把模块文件写出来，再 import"
    return True, "过关！项目拆成模块了，小K 的工程结构像样了。"
