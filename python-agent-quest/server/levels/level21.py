import ast

from server.runner import RunResult

ID = 21
TITLE = "Deep Agents 源码精读：Skills 发现与渐进式披露"

STORY = (
    "agent 的技能不是写死在代码里的。Deep Agents 启动时扫描目录里的 SKILL.md，"
    "只把「名字 + 描述」的索引注入 prompt，模型真要用某个技能时才去读全文——"
    "渐进式披露，省 token 的经典操作。这一关实现技能发现器。"
)

KNOWLEDGE = """\
Skills 发现——渐进式披露（progressive disclosure）。

1) 源码位置
  deepagents/middleware/skills.py：
  :591 _list_skills_with_errors 扫描目录里的 SKILL.md，解析出每个技能的名字和描述；
  :905 modify_request 把技能索引（只有名字+描述）注入 system prompt。
  全文不进 prompt——模型说「我要用这个技能」时才去读完整文件。

2) 渐进式披露
  先给目录，需要再取正文。一百个技能的原文全塞进 prompt，几万 token 没了；
  只塞索引，几百 token 搞定。和第 18 关的落盘是同一个思想：
  上下文里放引用，细节按需加载。

3) Java 对照
  Spring 的类路径扫描（@ComponentScan）先发现有哪些 bean，
  配合懒加载（@Lazy），真正用到时才初始化——发现与加载分离。

4) SKILL.md 长什么样
  开头一段 frontmatter（--- 包着的 name/desc 等元数据），后面是正文。
  扫描器只解析 frontmatter 生成索引——本关我们也只解析 name 和 desc 两行。
"""

STARTER_CODE = """\
# 任务：实现 discover_skills(fs)——扫描「文件系统」里的 SKILL.md，生成技能索引
# 1. 遍历 fs 里每个路径和内容
# 2. 按行解析出 name 和 desc（遇到 "name:" / "desc:" 开头的行就取冒号后面的值）
# 3. 返回索引字符串列表，格式："- 名字: 描述"
# 期望输出：
# 可用技能：
# - 查天气: 查询城市天气
# - 查股票: 查询股票价格

SKILLS_FS = {
    "weather/SKILL.md": "---\\nname: 查天气\\ndesc: 查询城市天气\\n---\\n正文略",
    "stock/SKILL.md": "---\\nname: 查股票\\ndesc: 查询股票价格\\n---\\n正文略",
}

def discover_skills(fs):
    index = []
    for path, content in fs.___():  # 填：items()，遍历每个「文件」
        name = desc = ""
        for line in content.split("\\n"):
            if line.___("name:"):   # 填：startswith，认出 name 行
                name = line.split(":", 1)[1].strip()
            if line.startswith("desc:"):
                desc = line.split(":", 1)[1].strip()
        index.append(f"- {___}: {___}")  # 填：名字和描述
    return index

print("可用技能：")
for line in discover_skills(SKILLS_FS):
    print(line)
"""

SOLUTION = """\
SKILLS_FS = {
    "weather/SKILL.md": "---\\nname: 查天气\\ndesc: 查询城市天气\\n---\\n正文略",
    "stock/SKILL.md": "---\\nname: 查股票\\ndesc: 查询股票价格\\n---\\n正文略",
}

def discover_skills(fs):
    index = []
    for path, content in fs.items():
        name = desc = ""
        for line in content.split("\\n"):
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
            if line.startswith("desc:"):
                desc = line.split(":", 1)[1].strip()
        index.append(f"- {name}: {desc}")
    return index

print("可用技能：")
for line in discover_skills(SKILLS_FS):
    print(line)
"""

EXPECTED_OUTPUT = "可用技能：\n- 查天气: 查询城市天气\n- 查股票: 查询股票价格"


def _has_for(fn: ast.FunctionDef) -> bool:
    return any(isinstance(node, ast.For) for node in ast.walk(fn))


def _has_string_parsing(fn: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("split", "startswith")
        for node in ast.walk(fn)
    )


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印三行：\n"
            "可用技能：\n- 查天气: 查询城市天气\n- 查股票: 查询股票价格"
        )
    tree = ast.parse(source)
    discover_fns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "discover_skills"
    ]
    if not discover_fns:
        return False, "结果对了，但本关要求定义 discover_skills(fs) 函数，不能直接打印答案"
    if not any(_has_for(fn) for fn in discover_fns):
        return False, "discover_skills 里要用 for 循环遍历文件系统——技能是扫描发现的，不能手写死索引"
    if not any(_has_string_parsing(fn) for fn in discover_fns):
        return False, "要真的解析 SKILL.md 内容（split / startswith 按行提取 name 和 desc），不能跳过解析直接拼结果"
    return True, "过关！先扫描出索引、需要时再读全文——渐进式披露，token 大省。"
