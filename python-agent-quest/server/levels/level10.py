import ast

from server.runner import RunResult

ID = 10
TITLE = "装饰器：@tool 注册"

STORY = (
    "看 LangChain 的源码，给函数加一个 @tool 它就变成了 agent 的工具，像魔法一样。"
    "这一关拆开这个魔法——亲手写一个自己的 @tool 注册器。"
)

KNOWLEDGE = """\
装饰器对比 Java 注解——长得像，本质完全不同：

1) Java 注解是元数据，Python 装饰器是可执行代码
  Java:   @Component
          public class SearchTool { ... }
  注解自己不干活，靠 Spring 启动时扫描、反射来处理。
  Python: @tool
          def search(query): ...
  @tool 等价于 search = tool(search)——在函数定义的那一刻就立即执行。

2) 为什么能这么玩？因为函数是一等公民
  Python 的函数可以当参数传、当返回值返回（Java 8 才补上 lambda 和方法引用）。
  装饰器就是一个「收一个函数、返回一个函数」的普通函数，没有任何特殊语法。

3) 典型用途：注册
  Flask 的 @app.route("/api")、LangChain 的 @tool，都是同一个套路：
  定义函数的同时把它登记进一张表，框架之后照表调用。
  思路和 Spring 的组件扫描一样，但 Python 是函数自己执行代码完成的，不需要容器。
"""

STARTER_CODE = """\
# 任务：写一个 @tool 装饰器，把被装饰的函数注册进 TOOL_REGISTRY
# 期望输出：
# 已注册工具：['search']
# 搜索：Python 教程

TOOL_REGISTRY = {}

def tool(func):
    ___  # 把 func.__name__ -> func 存进 TOOL_REGISTRY
    ___  # 返回 func（装饰器必须返回一个函数）

___  # 在这里给 search 加上装饰器
def search(query):
    return f"搜索：{query}"

print(f"已注册工具：{list(TOOL_REGISTRY.keys())}")
print(search("Python 教程"))
"""

SOLUTION = """\
TOOL_REGISTRY = {}

def tool(func):
    TOOL_REGISTRY[func.__name__] = func
    return func

@tool
def search(query):
    return f"搜索：{query}"

print(f"已注册工具：{list(TOOL_REGISTRY.keys())}")
print(search("Python 教程"))
"""

EXPECTED_OUTPUT = "已注册工具：['search']\n搜索：Python 教程"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "已注册工具：['search']\n搜索：Python 教程"
        )
    tree = ast.parse(source)
    funcs = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if "tool" not in funcs:
        return False, "结果对了，但本关要自己写一个 tool 装饰器函数，不能手动注册或直接打印答案"
    search = funcs.get("search")
    if search is None:
        return False, "被装饰的 search 函数要保留哦"
    has_tool_decorator = any(
        isinstance(deco, ast.Name) and deco.id == "tool"
        for deco in search.decorator_list
    )
    if not has_tool_decorator:
        return False, "search 要用 @tool 装饰来注册，不能手动 TOOL_REGISTRY[...] = search"
    return True, "过关！你拆开了 @tool 的魔法——它只是一个普通函数。"
