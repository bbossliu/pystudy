import ast

from server.runner import RunResult

ID = 6
TITLE = "函数：封装 LLM 调用"

STORY = (
    "小K 的思考循环跑起来了，但每次调 LLM 都要把拼装逻辑重写一遍，又乱又容易抄错。"
    "把「调用 LLM」这一步封装成函数，以后一行就能调用。"
)

KNOWLEDGE = """\
def 定义函数，对比 Java 方法——不用写返回类型和访问修饰符：

```plaintext
  Java:   String callLlm(String prompt, String model) { return ...; }
  Python: def call_llm(prompt, model="mock-1"):
              return ...
```

要点：
  - 默认参数 model="mock-1"：调用时不传就用默认值，相当于 Java 写两个重载方法
  - return 和 Java 一样；不写 return 的话默认返回 None
  - 命名习惯用蛇形 call_llm，而不是 Java 的驼峰 callLlm
  - Python 函数是一等公民，可以赋值给变量、当参数传（第 10 关装饰器就靠这个）
"""

STARTER_CODE = """\
# 任务：定义函数 call_llm(prompt, model="mock-1")，
# 返回 f"[{model}] 回复：{prompt} 的模拟回答"
# 然后调用两次并打印返回值：一次传 model="mock-pro"，一次用默认 model
# 期望输出：
# [mock-pro] 回复：你好 的模拟回答
# [mock-1] 回复：介绍一下你自己 的模拟回答

___ call_llm(prompt, model=___):  # 提示：def、默认值 "mock-1"
    return ___  # 用 f-string 拼出返回字符串

print(call_llm("你好", model="mock-pro"))
print(call_llm("介绍一下你自己"))
"""

SOLUTION = """\
def call_llm(prompt, model="mock-1"):
    return f"[{model}] 回复：{prompt} 的模拟回答"

print(call_llm("你好", model="mock-pro"))
print(call_llm("介绍一下你自己"))
"""

EXPECTED_OUTPUT = "[mock-pro] 回复：你好 的模拟回答\n[mock-1] 回复：介绍一下你自己 的模拟回答"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "[mock-pro] 回复：你好 的模拟回答\n"
            "[mock-1] 回复：介绍一下你自己 的模拟回答"
        )
    tree = ast.parse(source)
    funcs = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if "call_llm" not in funcs:
        return False, "结果对了，但本关要求把调用逻辑封装成 def call_llm(...) 函数，不能直接打印答案"
    if not funcs["call_llm"].args.defaults:
        return False, 'call_llm 要带默认参数 model="mock-1"，体会一下默认参数怎么代替 Java 的重载'
    return True, "过关！调用 LLM 被封装成一个函数了。"
