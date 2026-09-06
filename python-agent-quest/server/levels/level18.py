import ast

from server.runner import RunResult

ID = 18
TITLE = "Deep Agents 源码精读：大结果落盘（offloading）"

STORY = (
    "工具返回了 10MB 的日志，全塞进上下文会把模型撑爆——token 要钱，窗口有限。"
    "Deep Agents 的做法很干脆：超过阈值就写进 Backend，上下文里只留一个路径引用，"
    "模型需要细节时自己再去读。这一关给 MemoryBackend 装上这个能力。"
)

KNOWLEDGE = """\
Offloading——大结果落盘，上下文只留引用。

1) 源码位置
  deepagents/middleware/filesystem.py:3241 调用 _offload_tool_message_content：
  工具返回的内容超过阈值，就整个写进 Backend，tool message 里替换成
  一个指向文件路径的简短引用。

2) 解决什么问题？
  LLM 上下文窗口是稀缺资源。一次 grep 命中几千行、一次日志读取几 MB，
  原文塞进去，几轮对话就把窗口占满了。
  落盘后上下文里只有一行引用，模型想看细节可以用 read 工具按需读取——
  这就是「渐进式披露」的思想，后面技能系统还会再见到它。

3) Java 对照
  大对象存 OSS、数据库里只存 URL——完全同款思路。
  判定逻辑也一样：size > threshold 就走对象存储，否则直接内联。

4) 阈值怎么定？
  本关用 limit=20（字符数）做演示；真实系统按 token 数算。
  关键不是数值，是这个 if 分支：小结果直传，大结果转存。
"""

STARTER_CODE = """\
# 任务：实现 offload(content, backend, limit=20)——内容超阈值就落盘，只返回路径引用
# 规则：
#   1. len(content) <= limit：原样返回 content
#   2. 超过 limit：写入 backend（路径 /offload/result.txt），返回 "[结果过大，已保存到 /offload/result.txt]"
# 期望输出：
# 小结果
# [结果过大，已保存到 /offload/result.txt]
# 很长的日志

# ↓↓↓ 这是你在第 17 关写的 MemoryBackend，直接拿来用，不用改 ↓↓↓
class MemoryBackend:
    def __init__(self):
        self.files = {}

    def write(self, path, content):
        self.files[path] = content

    def read(self, path):
        return self.files[path]

    def ls(self):
        return list(self.files.keys())
# ↑↑↑ 第 17 关成果结束 ↑↑↑

def offload(content, backend, limit=20):
    if len(content) <= limit:
        return ___  # 没超阈值：原样返回
    backend.___("/offload/result.txt", content)  # 超了：写进 backend
    return "[结果过大，已保存到 /offload/result.txt]"

backend = MemoryBackend()
print(offload("小结果", backend))
print(offload("很长的日志" * 10, backend))
print(backend.read("/offload/result.txt")[:5])  # 看看落盘内容的前 5 个字符
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

def offload(content, backend, limit=20):
    if len(content) <= limit:
        return content
    backend.write("/offload/result.txt", content)
    return "[结果过大，已保存到 /offload/result.txt]"

backend = MemoryBackend()
print(offload("小结果", backend))
print(offload("很长的日志" * 10, backend))
print(backend.read("/offload/result.txt")[:5])
"""

EXPECTED_OUTPUT = "小结果\n[结果过大，已保存到 /offload/result.txt]\n很长的日志"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印三行：\n"
            "小结果\n[结果过大，已保存到 /offload/result.txt]\n很长的日志"
        )
    tree = ast.parse(source)
    offload_fns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "offload"
    ]
    if not offload_fns:
        return False, "结果对了，但本关要求定义 offload(content, backend, limit=20) 函数，不能直接打印答案"
    if not any(
        isinstance(node, ast.If)
        for fn in offload_fns for node in ast.walk(fn)
    ):
        return False, "offload 里要用 if 判断内容长度——小结果直传、大结果落盘，这个分支是核心"
    if not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write"
        for node in ast.walk(tree)
    ):
        return False, "超阈值的内容要调用 backend.write(...) 落盘，不能只在上下文里留个假引用"
    return True, "过关！大结果落盘了，上下文里只剩一行引用——模型的窗口省下来了。"
