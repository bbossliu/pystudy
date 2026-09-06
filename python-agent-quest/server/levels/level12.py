import ast

from server.runner import RunResult

ID = 12
TITLE = "async/await：并发调工具"

STORY = (
    "小K 干活时要同时查天气、搜资料、读文件，一个一个等太慢了。"
    "给它装上 async/await，让这些 IO 等待同时挂起、并发完成。"
)

KNOWLEDGE = """\
async/await 对比 Java 的线程模型——思路完全不同：

1) Java：多线程，抢占式调度
  Java 的并发靠 Thread（操作系统线程），多个线程真正同时跑在多核上，
  操作系统随时可以掐断一个线程换另一个——这叫抢占式。
  代码执行到一半都可能被切换，所以要加锁、上线程池，心智负担重。

2) Python asyncio：单线程，协作式调度
  async 代码全程只跑在一个线程里，核心是一个「事件循环」（event loop）。
  只有执行到 await（遇到 IO 等待）时，当前协程才主动让出控制权，
  事件循环趁机去跑别的协程——这叫协作式：你不 await，别人就没机会跑。
  好处是单线程内没有数据竞争，基本不用加锁；
  代价是协程里跑纯 CPU 重活会把所有人堵住。

3) 写法对照

```plaintext
  Java:   CompletableFuture<String> f =
              CompletableFuture.supplyAsync(() -> callTool(name));
          CompletableFuture.allOf(f1, f2, f3).join();
  Python: async def call_tool(name): ...
          results = await asyncio.gather(call_tool("查天气"), ...)
```

4) async def 只是定义协程函数，调用它不会执行，只得到一个协程对象；
  await 才真正等它跑完并拿到返回值。
  最外层用 asyncio.run(main()) 启动事件循环——它是异步世界的程序入口。

5) 为什么 agent 框架全是 async？
  agent 的时间大头在等 LLM 和工具的 IO 返回。async 用单线程就能同时挂起
  成百上千个等待，比开一堆线程省资源得多。
  LangChain / LangGraph 的 API 几乎都是 async 的——这是常态，不是炫技。
"""

STARTER_CODE = """\
# 任务：用 async/await 并发调用三个工具，逐个打印结果
# 期望输出（顺序固定为传入顺序）：
# 查天气 完成
# 搜资料 完成
# 读文件 完成

import asyncio

___ def call_tool(name):  # 提示：async def
    await asyncio.sleep(0)  # 模拟一次 IO 等待
    return f"{name} 完成"

async def main():
    tools = ["查天气", "搜资料", "读文件"]
    results = await asyncio.___(...)  # 提示：gather，把每个工具名包成 call_tool(name) 调用
    for r in results:
        print(r)

___  # 提示：asyncio.run(main())
"""

SOLUTION = """\
import asyncio

async def call_tool(name):
    await asyncio.sleep(0)
    return f"{name} 完成"

async def main():
    tools = ["查天气", "搜资料", "读文件"]
    results = await asyncio.gather(*[call_tool(name) for name in tools])
    for r in results:
        print(r)

asyncio.run(main())
"""

EXPECTED_OUTPUT = "查天气 完成\n搜资料 完成\n读文件 完成"


def _is_asyncio_call(node: ast.AST, attr: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attr
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "asyncio"
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印三行（顺序固定）：\n"
            "查天气 完成\n搜资料 完成\n读文件 完成"
        )
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    if not any(isinstance(node, ast.AsyncFunctionDef) for node in nodes):
        return False, "结果对了，但本关要求用 async def 定义协程函数，同步代码不算过关"
    if not any(isinstance(node, ast.Await) for node in nodes):
        return False, "协程里要用 await 等待异步操作"
    if not any(_is_asyncio_call(node, "gather") for node in nodes):
        return False, "并发调用多个协程要用 asyncio.gather(...)，不能一个个 await"
    if not any(_is_asyncio_call(node, "run") for node in nodes):
        return False, "最后要用 asyncio.run(main()) 启动事件循环"
    return True, "过关！小K 学会同时开工了——单线程也能并发等 IO。"
