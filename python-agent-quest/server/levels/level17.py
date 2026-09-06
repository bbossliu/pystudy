import ast

from server.runner import RunResult

ID = 17
TITLE = "Deep Agents 源码精读：Backend 协议（策略模式）"

STORY = (
    "agent 干活产生的上下文要落盘，但落到哪里——内存？本地文件？数据库？"
    "Deep Agents 的答案是：先定义一套统一协议（read/write/edit/ls……），"
    "实现随便换，上层代码一行不改。这一关我们写它的最小实现：内存版 Backend。"
)

KNOWLEDGE = """\
Backend 协议——面向接口编程，Python 风格。

1) 源码位置
  deepagents/backends/protocol.py:404 定义了 BackendProtocol：
  read / write / edit / ls 等一组标准方法。Deep Agents 内置了好几种实现——
  StateBackend（存内存）、FilesystemBackend（存真实文件）、StoreBackend（存数据库），
  上层 agent 代码完全不关心背后是哪一种。

2) Java 对照：接口 + 策略模式
  这就是你熟悉的 interface + 多实现注入。区别是 Python 用鸭子类型，
  连接口声明都省了——只要你的类有 write/read/ls 这些方法，
  它就是一个 Backend，可以直接传给任何需要 Backend 的地方。

3) 为什么需要这层抽象？
  测试时用内存版（快、不弄脏磁盘），跑真任务用文件版，分布式部署换数据库版——
  换实现不改业务代码，这就是策略模式的价值。

4) 内部结构
  内存版最简单：一个 dict 就够，path 当 key，content 当 value。
  ls() 就是 dict 的 keys。别小看它——第 18 关的大结果落盘就建在它的肩膀上。
"""

STARTER_CODE = """\
# 任务：实现 MemoryBackend——一个把「文件」存在内存 dict 里的 Backend
# write(path, content)：存进去；read(path)：按 path 取出；ls()：返回所有路径的列表
# 期望输出：
# 买牛奶
# ['/notes/todo.txt']

class MemoryBackend:
    def __init__(self):
        self.files = ___  # 填：一个空 dict

    def write(self, path, content):
        self.files[___] = content  # 填：用 path 当 key

    def read(self, path):
        return self.files[___]

    def ls(self):
        return ___(self.files.keys())  # 提示：转成 list

backend = MemoryBackend()
backend.write("/notes/todo.txt", "买牛奶")
print(backend.read("/notes/todo.txt"))
print(backend.ls())
"""

SOLUTION = """\
class MemoryBackend:
    def __init__(self):
        self.files = {}

    def write(self, path, content):
        self.files[path] = content

    def read(self, path):
        return self.files[path]

    def ls(self):
        return list(self.files.keys())

backend = MemoryBackend()
backend.write("/notes/todo.txt", "买牛奶")
print(backend.read("/notes/todo.txt"))
print(backend.ls())
"""

EXPECTED_OUTPUT = "买牛奶\n['/notes/todo.txt']"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "买牛奶\n['/notes/todo.txt']"
        )
    tree = ast.parse(source)
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    mem_cls = classes.get("MemoryBackend")
    if mem_cls is None:
        return False, "结果对了，但本关要求定义 MemoryBackend 类，不能直接打印答案"
    methods = {
        node.name for node in mem_cls.body if isinstance(node, ast.FunctionDef)
    }
    missing = {"write", "read", "ls"} - methods
    if missing:
        return False, f"MemoryBackend 还缺方法：{'、'.join(sorted(missing))}——协议要求 read/write/ls 三件套"
    return True, "过关！协议定好了，内存版 Backend 就绪——后面换实现不用改上层代码。"
