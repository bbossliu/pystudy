import ast

from server.runner import RunResult

ID = 38
TITLE = "生成器：用多少来多少"

STORY = (
    "小K 要处理 100 万行日志，一把全读进内存直接炸。"
    "生成器让数据「用多少来多少」——每次 yield 一个值就暂停，"
    "下次从这里接着跑。这也是 LLM 流式输出的底层思想。"
)

KNOWLEDGE = """\
生成器——yield 让数据「用多少来多少」。

1) 点题
  普通函数 return 一次给全部；生成器每次
  yield 一个值就暂停，下次从暂停处接着跑。
  百万行日志不必全进内存。

2) 核心用法
  def read():
      yield "日志1"
      yield "日志2"
  for line in read():   # 逐条拉取
      print(line)

3) Java 对照
  yield 暂停续跑 ≈ Java Iterator.next() 逐条取
  惰性求值       ≈ Java Stream：不遍历就不计算
  Java 要自己实现 hasNext/next 一套，
  Python 一个 yield 关键字就搞定。

4) 坑与边界
  函数里出现 yield，调用它就只返回生成器
  对象，函数体一行都不执行。
  生成器是一次性的：耗尽后再 for 就是空的，
  想再读一遍得重新调用造个新的。
  下图：next 拉一次，yield 吐一个并暂停。

5) 延伸
  对应莫烦 8.4「生成器」。
  LLM 的流式输出、逐行读大文件都是同款思想。
  数据量小、还要反复用时，直接列表更省事。
"""

STARTER_CODE = """\
# 任务：用生成器逐行「读」日志，内存里永远只有一条
# 1. 实现 read_logs()：用 yield 依次产出 日志1 / 日志2 / 日志3
# 2. 用 for 消费生成器，逐条打印（模板已给出）
# 期望输出：
# 读到：日志1
# 读到：日志2
# 读到：日志3

def read_logs():
    ___ "日志1"   # 填：产出值并暂停的关键字
    ___ "日志2"
    ___ "日志3"

for log in read_logs():
    print(f"读到：{log}")
"""

SOLUTION = """\
def read_logs():
    yield "日志1"
    yield "日志2"
    yield "日志3"

for log in read_logs():
    print(f"读到：{log}")
"""

EXPECTED_OUTPUT = "读到：日志1\n读到：日志2\n读到：日志3"

# 生成器惰性拉取：调用方每次 next → 产出一个值并暂停 → 再 next 再继续；对比普通函数一次性返回整个列表
DIAGRAM = r"""graph LR
    subgraph S1["普通函数：一次性给全部"]
        direction LR
        CALL1["调用 read()"] --> RET["return 整个列表<br>全部数据挤进内存"]
    end
    subgraph S2["生成器：拉一个给一个"]
        direction LR
        N1["next()"] --> Y1["yield 日志1<br>产出并暂停"]
        Y1 --> N2["next()"] --> Y2["yield 日志2<br>产出并暂停"]
        Y2 --> N3["next()"] --> Y3["yield 日志3<br>产出并暂停"]
    end
"""


def _has_yield_in_function(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(isinstance(inner, (ast.Yield, ast.YieldFrom)) for inner in ast.walk(node)):
                return True
    return False


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望逐条打印三行：\n"
            "读到：日志1\n读到：日志2\n读到：日志3"
        )
    tree = ast.parse(source)
    if not _has_yield_in_function(tree):
        return False, (
            "结果对了，但没看到 yield——函数里 return 列表是一次性给全部，"
            "本关要用 yield 让数据逐条产出、用多少来多少"
        )
    return True, "过关！yield 吐一个停一下——生成器这只水龙头你装上了。"
