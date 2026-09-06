import ast
import json
import os

from server.runner import RunResult

ID = 8
TITLE = "文件读写与 json：持久化记忆"

STORY = (
    "小K 现在能聊能扛错，但程序一关，记忆就全没了。"
    "把对话历史用 json 存进文件，让它下次醒来还记得你。"
)

KNOWLEDGE = """\
文件读写 + json，对比 Java：

```plaintext
  Java:   try (BufferedWriter w = Files.newBufferedWriter(path)) { ... }
          // 序列化还得引 Jackson / Gson 依赖
  Python: with open("memory.json", "w", encoding="utf-8") as f:
              json.dump(data, f, ensure_ascii=False)
```

要点：
  - with 会自动帮你关文件，等价于 Java 的 try-with-resources
  - json 是标准库自带，不用引依赖：json.dump 写、json.load 读
  - ensure_ascii=False 让中文原样保存，否则会变成 \\u4f60\\u597d 这种转义
  - "w" 是覆盖写、"r" 是读，和 Java 的打开模式一个意思
"""

STARTER_CODE = """\
# 任务：把对话记忆持久化到磁盘，再读回来验证
# 1. 用 with open + json.dump 把 messages 写进 memory.json（注意 ensure_ascii=False）
# 2. 再用 with open + json.load 读回来，打印：已保存 1 条记忆
# 期望输出：已保存 1 条记忆

import json

messages = [{"role": "user", "content": "你好"}]

with open("memory.json", "w", encoding="utf-8") as f:
    json.dump(messages, f, ensure_ascii=___)  # 填：False，让中文正常保存

with open(___, "r", encoding="utf-8") as f:  # 填：要读的文件名
    loaded = json.load(f)

print(f"已保存 {___} 条记忆")  # 填：loaded 的长度
"""

SOLUTION = """\
import json

messages = [{"role": "user", "content": "你好"}]

with open("memory.json", "w", encoding="utf-8") as f:
    json.dump(messages, f, ensure_ascii=False)

with open("memory.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)

print(f"已保存 {len(loaded)} 条记忆")
"""

EXPECTED_OUTPUT = "已保存 1 条记忆"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, "输出不对哦，期望打印：已保存 1 条记忆"
    memory_path = os.path.join(result.workdir, "memory.json")
    if not os.path.exists(memory_path):
        return False, "输出对了，但运行目录里没有 memory.json——记忆要真实写进文件，不能只打印一句话"
    try:
        with open(memory_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, "memory.json 里不是合法的 JSON，试试用 json.dump 来写"
    if not isinstance(data, list) or len(data) != 1:
        return False, "memory.json 里应该正好是 1 条记忆记录"
    tree = ast.parse(source)
    if not any(isinstance(node, ast.With) for node in ast.walk(tree)):
        return False, "文件读写请用 with open(...)，让 Python 自动帮你关文件"
    return True, "过关！小K 的记忆落盘了，重启也不怕。"
