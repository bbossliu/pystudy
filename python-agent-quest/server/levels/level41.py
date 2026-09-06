import ast

from server.runner import RunResult

ID = 41
TITLE = "线程与 GIL：写法眼熟，语义不同"

STORY = (
    "Java 人的直觉：开几个线程算几份活，速度快几倍。"
    "Python 里试一下——咦，没快？这就是 GIL：同一时刻只有一个线程"
    "在执行 Python 字节码。先用两个线程干点活，把写法和语义都看清。"
)

KNOWLEDGE = """\
线程与 GIL——写法眼熟，并发语义完全不同。

1) 点题
  多线程写法 Python 和 Java 几乎一样，
  但 GIL 让纯计算的多线程加不了速。

2) 核心用法

```plaintext
  import threading
  t = threading.Thread(target=worker,
                       args=(results,))
  t.start()   # 启动线程
  t.join()    # 等它干完再继续
```

3) Java 对照

```plaintext
  threading.Thread ≈ new Thread(runnable)
  start()/join()   ≈ start()/join()，名字一样
  GIL              ≈ JVM 没有这东西！
```
  同一时刻只有一个线程执行 Python 字节码，
  Java 多核是真并行，Python 线程是轮流跑。

4) 坑与边界
  纯 CPU 计算开多线程几乎不提速——GIL 卡着；
  要快用多进程 multiprocessing 或 numpy。
  IO 等待（网络/文件）时 GIL 会释放，
  所以 IO 并发多线程依然有效。
  共享列表 append 基本安全，计数器 += 不是。
  下图：两线程交替持有 GIL vs Java 双核并行。

5) 延伸
  对应莫烦 9.1「线程」。
  呼应 L12：IO 并发也可以选 async/await。
  重计算别硬刚线程，换多进程或交给 C 扩展。
"""

STARTER_CODE = """\
# 任务：起两个线程干活，join 等它们都完成
# 1. 实现 worker(name, results)：把 f"{name} 完成" append 进共享列表
# 2. 起两个线程分别跑 线程A 和 线程B
# 3. join 等待两个线程，然后排序打印 results 每条（模板已给出）
# 期望输出：
# 线程A 完成
# 线程B 完成

import threading

def worker(name, results):
    results.append(f"{name} ___")   # 填：表示「完成」的词

results = []

t1 = threading.___(target=worker, args=("线程A", results))  # 填：线程类
t2 = threading.___(target=worker, args=("线程B", results))

t1.start()
t2.start()

t1.___()   # 填：等线程干完的方法
t2.___()

for line in sorted(results):
    print(line)
"""

SOLUTION = """\
import threading

def worker(name, results):
    results.append(f"{name} 完成")

results = []

t1 = threading.Thread(target=worker, args=("线程A", results))
t2 = threading.Thread(target=worker, args=("线程B", results))

t1.start()
t2.start()

t1.join()
t2.join()

for line in sorted(results):
    print(line)
"""

EXPECTED_OUTPUT = "线程A 完成\n线程B 完成"

# GIL 时间轴：两线程交替持有 GIL（轮流跑） vs Java 双核真并行（同时跑）
DIAGRAM = r"""graph LR
    subgraph S1["Python：一把 GIL，两线程交替持有"]
        direction LR
        A1["线程A<br>持有 GIL 跑一段"] --> B1["线程B<br>抢到 GIL 跑一段"]
        B1 --> A2["线程A<br>再次持有 GIL"] --> B2["线程B<br>再次持有 GIL"]
    end
    subgraph S2["Java：双核真并行，同时跑"]
        direction LR
        C1["核心1：线程A 全程在跑"]
        C2["核心2：线程B 全程在跑"]
    end
"""


def _has_thread_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "Thread":
            return True
        # 兼容 from threading import Thread 的写法
        if isinstance(func, ast.Name) and func.id == "Thread":
            return True
    return False


def _has_join_call(tree: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "join"
        for node in ast.walk(tree)
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望排序后逐行打印：\n"
            "线程A 完成\n线程B 完成"
        )
    tree = ast.parse(source)
    if not _has_thread_call(tree):
        return False, (
            "结果对了，但没看到 threading.Thread——"
            "本关要真起线程干活，别直接往列表里塞答案"
        )
    if not _has_join_call(tree):
        return False, (
            "结果对了，但没看到 join——不 join 主线程可能抢先打印，"
            "起完线程记得 t.join() 等它干完"
        )
    return True, "过关！Thread 起步、join 收尾——GIL 的来龙去脉你也看清了。"
