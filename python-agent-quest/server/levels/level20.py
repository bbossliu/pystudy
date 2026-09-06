import ast

from server.runner import RunResult

ID = 20
TITLE = "Deep Agents 源码精读：上下文压缩（summarization）"

STORY = (
    "和用户聊了 100 轮，上下文窗口眼看要炸了。Deep Agents 在用量逼近上限时触发压缩："
    "旧消息汇总成一段摘要，原文落盘可回溯，最近几轮原样保留。"
    "这一关给迷你 agent 装上这个「垃圾回收器」。"
)

KNOWLEDGE = """\
上下文压缩——对话太长时的「垃圾回收」。

1) 源码位置
  deepagents/middleware/summarization.py：
  :262 compute_summarization_defaults 根据模型窗口算出默认触发阈值（用量到约 85% 触发）；
  :734 _build_new_messages_with_path 用一条摘要消息替换整段旧历史；
  :1189 _offload_to_backend 把旧历史原文写进 Backend，随时可回溯。

2) 三步走
  触发：token 用量逼近窗口上限 → 摘要：让模型把旧消息压成一段 →
  落盘：原文存进文件，摘要里带上路径，想看原文随时读回来。
  旧消息不是删了，是「归档」了。

3) Java 对照：JVM GC
  内存不够不是无限扩容，而是回收整理：把不常用的旧对象压缩、挪走，
  腾出空间继续跑。上下文窗口就是 agent 的堆内存。

4) 保留最近几条
  压缩不是全压——最近几轮（keep）原样保留，
  因为模型紧接着就要接着它们往下说。全压成摘要，话就接不上了。
"""

STARTER_CODE = """\
# 任务：实现 compress(messages, backend, keep=2)——上下文要炸了，压缩！
# 1. 除最后 keep 条外的消息，用 fake_summarize 汇总成一条 system 消息：
#    {"role": "system", "content": "摘要：..."}
# 2. 被压缩的旧消息原文写入 backend 的 /history/archive.txt（一行一条，方便回溯）
# 3. 返回 [摘要消息] + 最后 keep 条
# 期望输出：
# 摘要：第一轮 第二轮
# 第三轮
# 第四轮
# 归档了 2 条

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

def fake_summarize(messages):
    # 模拟 LLM 生成摘要（离线版：把内容用空格拼成一行）
    return " ".join(m["content"] for m in messages)

def compress(messages, backend, keep=2):
    old = messages[:___]      # 填：切片，除了最后 keep 条（提示：-keep）
    recent = messages[___:]   # 填：切片，最后 keep 条（提示：-keep）
    summary = {"role": "system", "content": "摘要：" + fake_summarize(old)}
    backend.___("/history/archive.txt", "\\n".join(m["content"] for m in old))  # 填：落盘方法
    return [___] + recent     # 填：摘要消息放最前面

messages = [
    {"role": "user", "content": "第一轮"},
    {"role": "user", "content": "第二轮"},
    {"role": "user", "content": "第三轮"},
    {"role": "user", "content": "第四轮"},
]
backend = MemoryBackend()
for m in compress(messages, backend):
    print(m["content"])
archived = backend.read("/history/archive.txt")
print(f"归档了 {len(archived.splitlines())} 条")
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

def fake_summarize(messages):
    return " ".join(m["content"] for m in messages)

def compress(messages, backend, keep=2):
    old = messages[:-keep]
    recent = messages[-keep:]
    summary = {"role": "system", "content": "摘要：" + fake_summarize(old)}
    backend.write("/history/archive.txt", "\\n".join(m["content"] for m in old))
    return [summary] + recent

messages = [
    {"role": "user", "content": "第一轮"},
    {"role": "user", "content": "第二轮"},
    {"role": "user", "content": "第三轮"},
    {"role": "user", "content": "第四轮"},
]
backend = MemoryBackend()
for m in compress(messages, backend):
    print(m["content"])
archived = backend.read("/history/archive.txt")
print(f"归档了 {len(archived.splitlines())} 条")
"""

EXPECTED_OUTPUT = "摘要：第一轮 第二轮\n第三轮\n第四轮\n归档了 2 条"


def _has_slice(fn: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice)
        for node in ast.walk(fn)
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印四行：\n"
            "摘要：第一轮 第二轮\n第三轮\n第四轮\n归档了 2 条"
        )
    tree = ast.parse(source)
    compress_fns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "compress"
    ]
    if not compress_fns:
        return False, "结果对了，但本关要求定义 compress(messages, backend, keep=2) 函数，不能直接打印答案"
    if not any(_has_slice(fn) for fn in compress_fns):
        return False, "compress 里要用切片（messages[:-keep] 这类）切分新旧消息——一刀切出「要压缩的」和「要保留的」"
    if not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write"
        for node in ast.walk(tree)
    ):
        return False, "被压缩的旧消息要调用 backend.write(...) 落盘归档——摘要可回溯靠的就是这份原文"
    return True, "过关！旧历史压成摘要、原文落盘可回溯——agent 的「垃圾回收器」上线了。"
