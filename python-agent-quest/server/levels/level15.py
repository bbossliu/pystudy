import ast

from server.runner import RunResult

ID = 15
TITLE = "Deep Agents 源码精读：中间件洋葱模型"

STORY = (
    "欢迎来到 Deep Agents 源码精读系列！小K 的功能越加越多——记笔记、读文件、派子代理……"
    "全堆在一个函数里，代码变成一锅粥。Deep Agents 的答案是中间件："
    "每个功能都是包在 LLM 调用外的一层「洋葱皮」，请求一层层进，响应一层层出。"
    "这一关我们徒手搭出它的核心机制。"
)

KNOWLEDGE = """\
中间件（middleware）——Deep Agents 的地基。

1) 源码位置
  deepagents/middleware/__init__.py:15-47 讲清了核心契约：
  中间件继承 AgentMiddleware，重写 wrap_model_call(request, handler)，
  就能拦截每一次发给 LLM 的请求——改 prompt、换工具、压缩上下文，全靠这个钩子。

2) handler 是什么？
  handler 是「调用下一层」的函数。你的中间件拿到 request，可以做点手脚，
  然后调 handler(request) 把请求往下一层传，拿到结果后还能再加工返回。

3) Java 对照：Servlet Filter 链 / Spring Interceptor
  Java 里 Filter.doFilter(request, response, chain) 里的 chain.doFilter()
  就是这里的 handler(request)——一个显式的「放行」动作。
  区别是 Python 不用配置 web.xml，一串函数套一串函数就完事了。

4) 洋葱模型（onion model）
  中间件 A 套 B 套 C：请求 A→B→C→LLM，响应 LLM→C→B→A。
  先进去的后出来，像剥洋葱一样一层包一层。
  打印日志的中间件会打出「进入 A、进入 B、离开 B、离开 A」的对称结构。

5) 为什么这么设计？
  每个功能（记笔记、压缩上下文、注入技能）都是独立的一层皮，
  想加就加、想拆就拆，主流程一行不用动——这就是开闭原则的活例子。
"""

STARTER_CODE = """\
# 任务：给 LLM 调用包上中间件（洋葱模型）
# 1. Middleware 基类：wrap_model_call(self, request, handler) 默认直接调 handler 放行
# 2. LogMiddleware：调用 handler 前后各打印一行，观察洋葱的进出顺序
# 3. run_with_middleware(request, middlewares)：把中间件列表串成调用链
# 期望输出：
# >> 进入 LogMiddleware
# << 离开 LogMiddleware
# LLM 回复

def call_model(request):
    # 模拟一次 LLM 调用（离线版，直接返回固定回复）
    return "LLM 回复"

class Middleware:
    def wrap_model_call(self, request, handler):
        return ___(request)  # 默认实现：什么都不做，直接调 handler 放行

class LogMiddleware(Middleware):
    def wrap_model_call(self, request, handler):
        print(">> 进入 LogMiddleware")
        result = ___(request)  # 调 handler，让请求继续往下走
        print("<< 离开 LogMiddleware")
        return result

def run_with_middleware(request, middlewares):
    # 从里往外逐层包装：最后包的中间件最先收到请求
    handler = call_model
    for mw in reversed(middlewares):
        inner = handler
        handler = lambda req, mw=mw, inner=inner: mw.___(req, inner)  # 提示：wrap_model_call
    return ___(request)  # 从最外层的 handler 开始调用

result = run_with_middleware("你好", [LogMiddleware()])
print(result)
"""

SOLUTION = """\
def call_model(request):
    return "LLM 回复"

class Middleware:
    def wrap_model_call(self, request, handler):
        return handler(request)

class LogMiddleware(Middleware):
    def wrap_model_call(self, request, handler):
        print(">> 进入 LogMiddleware")
        result = handler(request)
        print("<< 离开 LogMiddleware")
        return result

def run_with_middleware(request, middlewares):
    handler = call_model
    for mw in reversed(middlewares):
        inner = handler
        handler = lambda req, mw=mw, inner=inner: mw.wrap_model_call(req, inner)
    return handler(request)

result = run_with_middleware("你好", [LogMiddleware()])
print(result)
"""

EXPECTED_OUTPUT = ">> 进入 LogMiddleware\n<< 离开 LogMiddleware\nLLM 回复"


def _calls_handler(method: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "handler"
        for node in ast.walk(method)
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印三行（注意顺序：日志在前，结果最后）：\n"
            ">> 进入 LogMiddleware\n<< 离开 LogMiddleware\nLLM 回复"
        )
    tree = ast.parse(source)
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if "Middleware" not in classes:
        return False, "结果对了，但本关要求定义 Middleware 基类，不能直接打印答案"
    if "run_with_middleware" not in functions:
        return False, "缺一个 run_with_middleware 函数把中间件串成链"
    log_cls = classes.get("LogMiddleware")
    if log_cls is None:
        return False, "还要写一个 LogMiddleware 类，观察请求的进出"
    wrap_methods = [
        node for node in log_cls.body
        if isinstance(node, ast.FunctionDef) and node.name == "wrap_model_call"
    ]
    if not wrap_methods:
        return False, "LogMiddleware 要重写 wrap_model_call(request, handler) 方法"
    if not any(_calls_handler(m) for m in wrap_methods):
        return False, "wrap_model_call 里要调用 handler(request) 放行请求，光打印不算中间件"
    return True, "过关！你搭出了中间件洋葱模型——这正是 Deep Agents 每个功能外挂的方式。"
