import ast

from server.runner import RunResult

ID = 16
TITLE = "Deep Agents 源码精读：System prompt 分层组装"

STORY = (
    "打开 Deep Agents 的源码你会发现：它的主 prompt 不是一坨几百行的字符串，"
    "而是分层的——基础 prompt、各中间件注入的片段、工具描述，一块一块拼出来的。"
    "这一关我们复刻这个拼装过程。"
)

KNOWLEDGE = """\
分层组装 system prompt——prompt 也是组装出来的。

1) 源码位置
  deepagents/graph.py:639-648 是基础拼装：profile 的基础 prompt 和
  用户传入的 system_prompt 用 "\\n\\n" 拼在一起；
  deepagents/middleware/_utils.py 里的 append_to_system_message
  是中间件们共用的工具——每个中间件都可以往 system prompt 后面追加自己的一段。

2) 为什么要分层？
  记忆中间件注入「用户偏好」，技能中间件注入「可用技能索引」，文件中间件注入
  「文件操作指南」——各自管各自的一段，互不干扰。
  想关掉某个功能？把对应的中间件从列表里删掉，prompt 自然就少了一段。

3) Java 对照
  像 StringBuilder 的链式 append，或者模板引擎里的片段（fragment）组合：
  每个模块只贡献自己的一块，最后统一渲染。
  比一坨大字符串好维护得多——改哪段去哪段的地盘改。

4) 分隔符的讲究
  片段之间用空行（"\\n\\n"）隔开，让 LLM 能看清段落边界。
  Python 里 "\\n\\n".join(parts) 一行搞定，不用手写循环加换行。
"""

STARTER_CODE = """\
# 任务：实现 build_prompt(base, injections)，把基础 prompt 和注入片段拼成完整 prompt
# 规则：所有片段之间用空行（\\n\\n）隔开
# 期望输出：
# 你是小K，一个代码助手。
#
# 可用工具：search、read_file
#
# 当前用户：小明

BASE_PROMPT = "你是小K，一个代码助手。"

def build_prompt(base, injections):
    parts = [base] + injections
    return ___.___(parts)  # 提示："\\n\\n".join(parts)

prompt = build_prompt(BASE_PROMPT, ["可用工具：search、read_file", "当前用户：小明"])
print(prompt)
"""

SOLUTION = """\
BASE_PROMPT = "你是小K，一个代码助手。"

def build_prompt(base, injections):
    parts = [base] + injections
    return "\\n\\n".join(parts)

prompt = build_prompt(BASE_PROMPT, ["可用工具：search、read_file", "当前用户：小明"])
print(prompt)
"""

EXPECTED_OUTPUT = "你是小K，一个代码助手。\n\n可用工具：search、read_file\n\n当前用户：小明"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印组装后的完整 prompt（片段之间有空行）：\n"
            "你是小K，一个代码助手。\n\n可用工具：search、read_file\n\n当前用户：小明"
        )
    tree = ast.parse(source)
    build_fns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "build_prompt"
    ]
    if not build_fns:
        return False, "结果对了，但本关要求定义 build_prompt(base, injections) 函数来拼装，不能整段写死"
    for fn in build_fns:
        has_join = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            for node in ast.walk(fn)
        )
        has_loop = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(fn))
        if has_join or has_loop:
            return True, "过关！prompt 是拼出来的，不是写出来的——这就是 Deep Agents 的分层思路。"
    return False, (
        "build_prompt 里要用 \"\\n\\n\".join(...)（或循环）把片段组装起来，"
        "直接返回写死的整段字符串不算过关"
    )
