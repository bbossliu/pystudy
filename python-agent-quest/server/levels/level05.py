import ast

from server.runner import RunResult

ID = 5
TITLE = "for 与推导式：Agent 的思考循环"

STORY = (
    "路由器上线了，小K 知道该干嘛了。但一个真正的 agent 不是一步到位，"
    "而是「思考 → 行动」反复迭代——现在给它装上主循环，这是所有 agent 框架的核心。"
)

KNOWLEDGE = """\
for 循环对比 Java 的增强 for：

```plaintext
  Java:   for (String s : steps) { ... }
  Python: for s in steps:
              ...
```

带编号用 enumerate(steps, 1)，序号从 1 开始；while 写法和 Java 一样。

列表推导式一步生成新列表，对比 Stream API 的 map + collect：

```plaintext
  Java:   steps.stream().map(s -> s + "-完成").collect(Collectors.toList())
  Python: [s + "-完成" for s in steps]
```
"""

STARTER_CODE = """\
# 任务①：用 for 循环带编号逐行打印每个步骤（提示：enumerate(steps, 1)）
# 任务②：用列表推导式给每步加上「-完成」标记，生成新列表并打印
# 期望输出：
# 步骤 1：理解问题
# 步骤 2：搜索资料
# 步骤 3：生成回答
# ['理解问题-完成', '搜索资料-完成', '生成回答-完成']

steps = ["理解问题", "搜索资料", "生成回答"]

for ___ in ___:  # 填：用 enumerate 同时拿到编号和步骤
    print(___)   # 填：用 f-string 打印「步骤 编号：步骤名」

done_steps = [___ for ___ in ___]  # 填：列表推导式，给每步加「-完成」
print(done_steps)
"""

SOLUTION = """\
steps = ["理解问题", "搜索资料", "生成回答"]
for i, step in enumerate(steps, 1):
    print(f"步骤 {i}：{step}")
done_steps = [f"{s}-完成" for s in steps]
print(done_steps)
"""

EXPECTED_OUTPUT = (
    "步骤 1：理解问题\n"
    "步骤 2：搜索资料\n"
    "步骤 3：生成回答\n"
    "['理解问题-完成', '搜索资料-完成', '生成回答-完成']"
)


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印：\n"
            "步骤 1：理解问题\n"
            "步骤 2：搜索资料\n"
            "步骤 3：生成回答\n"
            "['理解问题-完成', '搜索资料-完成', '生成回答-完成']"
        )
    tree = ast.parse(source)
    has_for = any(isinstance(node, ast.For) for node in ast.walk(tree))
    if not has_for:
        return False, "结果对了，但第①步要用 for 循环逐行打印，别手写三行 print"
    has_listcomp = any(isinstance(node, ast.ListComp) for node in ast.walk(tree))
    if not has_listcomp:
        return False, "结果对了，但第②步要用列表推导式 [... for ... in ...] 生成新列表"
    return True, "过关！小K 的思考循环跑起来了，这已经是 agent 框架的雏形。"
