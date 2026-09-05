import ast
import os

from server.runner import RunResult

ID = 14
TITLE = "真实 LLM：接入 DeepSeek"
TIMEOUT = 60

STORY = (
    "mock_llm 完成了它的使命。现在给 agent 换上真正的大脑——DeepSeek。"
    "通关后你的 agent 就是一个真实可用的 LLM 应用。"
)

KNOWLEDGE = """\
这一关没有新语法，只有一步关键的"接线"：把 mock_llm 换成真实的 DeepSeek API。

1. DeepSeek 兼容 OpenAI API，用官方 openai SDK，改一下 base_url 就行：

     from openai import OpenAI
     client = OpenAI(base_url="https://api.deepseek.com", api_key=...)

2. API key 绝不写进代码，从环境变量读：

     import os
     api_key = os.environ.get("DEEPSEEK_API_KEY")

   对比 Java：这就是 System.getenv("DEEPSEEK_API_KEY")。
   Java 里你不会把数据库密码硬编码进源码，这里也一样——
   key 一旦提交进 git，就等于公开了。

3. messages 参数就是第 3 关学的 dict 列表：

     resp = client.chat.completions.create(
         model="deepseek-chat",
         messages=[{"role": "user", "content": "你好"}],
     )
     print(resp.choices[0].message.content)

   对比 Java：相当于 RestTemplate/WebClient 发 POST，
   只是 SDK 帮你把 HTTP 细节都包好了。
"""

STARTER_CODE = """\
# 任务：给 agent 接上真实的 DeepSeek 大脑
# 要求：
#   1. 定义函数 llm_reply(user_input)，用 openai SDK 调 DeepSeek（model="deepseek-chat"）
#   2. API key 用 os.environ.get("DEEPSEEK_API_KEY") 读取，绝不能写进代码
#   3. 打印：小K：{回复内容}
# 运行本关前，确认启动服务的环境里已设置 DEEPSEEK_API_KEY。

import os

from openai import OpenAI


def llm_reply(user_input):
    client = OpenAI(
        base_url="https://api.deepseek.com",
        api_key=___,  # 填：从环境变量读 key
    )
    resp = client.chat.completions.create(
        model=___,  # 填：DeepSeek 的模型名
        messages=___,  # 填：dict 列表，role 为 "user"
    )
    return ___  # 填：回复的文本内容（resp.choices[0].message...）


if __name__ == "__main__":
    reply = llm_reply("用一句话介绍你自己")
    print(___)  # 填：小K：{回复}
"""

SOLUTION = """\
import os

from openai import OpenAI


def llm_reply(user_input):
    client = OpenAI(
        base_url="https://api.deepseek.com",
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
    )
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": user_input}],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    reply = llm_reply("用一句话介绍你自己")
    print(f"小K：{reply}")
"""


def _dotted_name(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        return False, "服务器没有配置 DEEPSEEK_API_KEY，先在启动服务的环境里设置它"
    if "sk-" in source:
        return False, (
            "检测到代码里有 sk- 开头的字符串——API key 不能硬编码，"
            '要用 os.environ.get("DEEPSEEK_API_KEY") 从环境变量读取'
        )
    if result.exit_code != 0:
        if "401" in result.stderr or "Authentication" in result.stderr:
            return False, "DeepSeek 返回 401 认证失败——API key 可能不对，检查 DEEPSEEK_API_KEY 是否有效"
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if "小K：" not in result.stdout:
        return False, "输出里没看到「小K：」——记得按格式打印：print(f\"小K：{回复}\")"
    tree = ast.parse(source)
    called = {_dotted_name(node.func) for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))}
    if not ({"os.environ.get", "os.getenv"} & called):
        return False, "输出对了，但 key 要用 os.environ.get（或 os.getenv）从环境变量读，不能写死在代码里"
    if not any(name == "OpenAI" or name.endswith(".OpenAI") for name in called):
        return False, "输出对了，但本关要真的构造 OpenAI client 调 DeepSeek，不能只打印固定答案"
    return True, "通关！你的 agent 接上了真实的大脑——它现在是一个真正能跑的 LLM 应用了。"
