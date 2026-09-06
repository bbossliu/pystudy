import ast

from server.runner import RunResult

ID = 22
TITLE = "Deep Agents 源码精读：收口——手写 create_my_deep_agent"

STORY = (
    "中间件、Backend、落盘、子代理、压缩、技能……机制都拆开学过一遍了。"
    "最后一关，把它们装回去：写一个你自己的 create_deep_agent。"
    "你会发现它没什么魔法——就是一条按固定顺序装配的流水线。"
)

KNOWLEDGE = """\
create_deep_agent——不是新引擎，是「预制装配厂」。

1) 源码位置
  deepagents/graph.py:271 的 create_deep_agent：一个几百行的函数，
  做的事就是按顺序组装——解析模型、拼 system prompt、
  按固定顺序摆好中间件栈、注册 task 等内置工具，
  最后 :956 一行 return create_agent(...) 委托给 LangChain 的标准引擎。

2) 真相
  Deep Agents 没有发明新的 agent 运行时。它真正的价值是「默认值」：
  什么中间件该有、按什么顺序叠、prompt 怎么写——这些踩过坑的配置
  它帮你预制好了。你这八关学的每个机制，都是流水线上的一个工位。

3) Java 对照：Spring Boot 自动配置
  spring-boot-autoconfigure 不发明新功能，它只是把 DataSource、
  Jackson、内嵌 Tomcat 按合理默认装配好。create_deep_agent 干的是同一件事。

4) 闭包：先装配、后调用
  create 函数返回一个 agent(request) 函数——装配只做一次，
  之后每次调用都复用这条装好的链。Python 用闭包实现，
  Java 里对应「工厂方法返回一个配置好的对象」。

5) 洋葱顺序再强调
  中间件栈 [A, B]：请求 A→B→LLM，响应 LLM→B→A。
  本关输出里两对「进入/离开」的对称结构，就是洋葱模型的指纹。
"""

STARTER_CODE = """\
# 任务：实现 create_my_deep_agent(middlewares)——你自己的「预制装配厂」
# 1. 创建时打印一次：装配了 {n} 个中间件
# 2. 返回一个 agent(request) 函数（闭包），调用时用第 15 关的中间件链处理 request
# 期望输出（注意嵌套顺序：第一个进的后出，像剥洋葱）：
# 装配了 2 个中间件
# >> 进入 LogMiddleware
# >> 进入 LogMiddleware
# << 离开 LogMiddleware
# << 离开 LogMiddleware
# LLM 回复

# ↓↓↓ 这是你在第 15 关写的中间件骨架，直接拿来用，不用改 ↓↓↓
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
# ↑↑↑ 第 15 关成果结束 ↑↑↑

def create_my_deep_agent(middlewares):
    print(f"装配了 {___(middlewares)} 个中间件")  # 填：len，数一下装配了几个
    def agent(request):
        return ___(request, middlewares)  # 填：第 15 关的串链函数
    return ___  # 填：返回这个闭包（注意：是函数本身，不是调用它）

agent = create_my_deep_agent([LogMiddleware(), LogMiddleware()])
print(agent("你好"))
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

def create_my_deep_agent(middlewares):
    print(f"装配了 {len(middlewares)} 个中间件")
    def agent(request):
        return run_with_middleware(request, middlewares)
    return agent

agent = create_my_deep_agent([LogMiddleware(), LogMiddleware()])
print(agent("你好"))
"""

EXPECTED_OUTPUT = (
    "装配了 2 个中间件\n"
    ">> 进入 LogMiddleware\n"
    ">> 进入 LogMiddleware\n"
    "<< 离开 LogMiddleware\n"
    "<< 离开 LogMiddleware\n"
    "LLM 回复"
)


def _has_closure(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.FunctionDef) and node is not fn:
            return True
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Lambda):
            return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印六行（嵌套顺序是关键：第一个进的后出，像剥洋葱）：\n"
            "装配了 2 个中间件\n"
            ">> 进入 LogMiddleware\n>> 进入 LogMiddleware\n"
            "<< 离开 LogMiddleware\n<< 离开 LogMiddleware\n"
            "LLM 回复"
        )
    tree = ast.parse(source)
    create_fns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "create_my_deep_agent"
    ]
    if not create_fns:
        return False, "结果对了，但本关要求定义 create_my_deep_agent(middlewares) 函数，不能直接打印答案"
    if not any(_has_closure(fn) for fn in create_fns):
        return False, (
            "create_my_deep_agent 要返回一个 agent(request) 闭包（或 lambda）——"
            "「先装配一次、后反复调用」才是装配厂"
        )
    return True, (
        "通关！你读完了 Deep Agents 的核心骨架：中间件、Backend、落盘、子代理、压缩、技能、装配。"
        "接下来可以去读真源码、跑真库了——你手里已经有地图了。"
    )
