import ast

from server.runner import RunResult

ID = 39
TITLE = "文件目录管理：pathlib 批量找文件"

STORY = (
    "小K 的记忆文件攒了一堆在目录里，要批量找出所有 .json 来处理。"
    "还在 os.listdir 加字符串拼路径？路径分隔符、后缀过滤全得手写。"
    "pathlib 是现代写法——一个 Path 对象全部搞定。"
)

KNOWLEDGE = """\
pathlib——面向对象的目录管理，告别拼路径。

1) 点题
  找文件、拼路径、取文件名，用 Path 对象
  一气呵成，比 os.listdir 手写拼接清爽。

2) 核心用法

```plaintext
  from pathlib import Path
  for p in Path(".").glob("*.json"):
      print(p.name)   # 文件名   a.json
      print(p.stem)   # 去掉后缀 a
```

3) Java 对照

```plaintext
  Path(".")      ≈ Java Paths.get(".")
  glob("*.json") ≈ Files.walk 加通配过滤
  p.name/p.stem  ≈ getFileName()、手动去后缀
  Path("a") / "b.txt" ≈ Paths.get("a", "b.txt")
```

4) 坑与边界
  glob 只匹配当前目录，不递归；
  递归要用 rglob("**/*.json")。
  Mac 的 / 和 Windows 的 \\ 交给 pathlib，
  别再 "/" + name 自己拼。
  glob 的返回顺序没保证，要排序用 sorted()。

5) 延伸
  对应莫烦 5.2「目录管理」。
  只拼一个路径时 os.path.join 也能凑合；
  批量遍历、要跨平台时才显出 pathlib 的香。
"""

STARTER_CODE = """\
# 任务：批量找出当前目录里的 .json 记忆文件
# 1. 先创建 3 个文件：a.json、b.json、c.txt（已给出）
# 2. 用 pathlib 的 glob 找出所有 .json 文件
# 3. 排序后逐行打印文件名
# 期望输出：
# a.json
# b.json

from pathlib import ___   # 填：面向对象的路径类

# 先造三个测试文件
Path("a.json").touch()
Path("b.json").touch()
Path("c.txt").touch()

json_files = ___(Path(".").glob("*.json"))   # 填：排序函数
for p in json_files:
    print(p.___)   # 填：只要文件名（含后缀）的属性
"""

SOLUTION = """\
from pathlib import Path

Path("a.json").touch()
Path("b.json").touch()
Path("c.txt").touch()

json_files = sorted(Path(".").glob("*.json"))
for p in json_files:
    print(p.name)
"""

EXPECTED_OUTPUT = "a.json\nb.json"


def _uses_path(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "Path":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "Path":
            return True
    return False


def _has_call(tree: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == name
        for node in ast.walk(tree)
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望排序后逐行打印两个 json 文件名：\n"
            "a.json\nb.json"
        )
    tree = ast.parse(source)
    if not _uses_path(tree):
        return False, (
            "结果对了，但没看到 pathlib 的 Path——"
            "别用 os.listdir 字符串过滤，from pathlib import Path 才是现代写法"
        )
    if not _has_call(tree, "glob"):
        return False, (
            "结果对了，但没看到 glob——批量找文件要用 "
            'Path(".").glob("*.json")，别手写后缀判断'
        )
    return True, "过关！Path.glob 一网打尽——目录管理的现代写法到手。"
