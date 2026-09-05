import ast

from server.runner import RunResult

ID = 9
TITLE = "class：Tool 与 Agent"

STORY = (
    "功能越加越多，散装的变量和函数快 hold 不住了。"
    "用 class 把「工具」和「Agent」组织成对象——LangChain 这些框架就是这么搭起来的。"
)

KNOWLEDGE = """\
class 对比 Java——处处相似，细节不同：

1) 定义与构造器
  Java:   public class Tool {
              private String name;
              public Tool(String name) { this.name = name; }
              public String describe() { return "工具：" + this.name; }
          }
  Python: class Tool:
              def __init__(self, name):
                  self.name = name
              def describe(self):
                  return f"工具：{self.name}"

2) self 要显式写出来
  Java 的 this 是隐式的，方法签名里看不到它；
  Python 每个方法的第一个参数都是 self，但调用时不用传——Python 会自动把对象塞进去。

3) __init__ 就是构造器
  双下划线是 Python 的「魔法方法」约定，__init__ 在创建对象时自动调用，类似 Java 的构造器。

4) 没有 private 关键字
  所有属性默认公开。约定俗成：名字前加一个下划线 _name 表示「内部使用，别乱动」，全靠自觉。

5) 不用写接口，duck typing
  Java 要先定义 interface 再 implements；
  Python 只要对象有同名方法就能互换——「走起来像鸭子，那就是鸭子」。

6) 没有 getter/setter 的负担
  属性直接 obj.name 读写；以后想加校验，可以用 @property 平滑升级，调用方无感。
"""

STARTER_CODE = """\
# 任务：用 class 把工具和 agent 组织起来
# class Tool：__init__ 收 name；describe() 返回 f"工具：{self.name}"
# class Agent：__init__ 收 name（自带空工具列表）；add_tool(tool) 添加工具；
#             status() 返回 f"Agent {self.name} 已装配 {len(self.tools)} 个工具"
# 期望输出：
# 工具：搜索
# Agent 小K 已装配 1 个工具

class Tool:
    def __init__(self, name):
        self.name = ___  # 填：把参数存到对象上

    def describe(self):
        return ___  # 用 f-string 返回描述

class Agent:
    def __init__(self, name):
        self.name = name
        self.tools = ___  # 填：一个空列表

    def add_tool(self, tool):
        self.tools.append(tool)

    def status(self):
        return f"Agent {self.name} 已装配 {len(self.tools)} 个工具"

tool = Tool("搜索")
agent = Agent("小K")
agent.add_tool(tool)

print(tool.describe())
print(agent.status())
"""

SOLUTION = """\
class Tool:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return f"工具：{self.name}"

class Agent:
    def __init__(self, name):
        self.name = name
        self.tools = []

    def add_tool(self, tool):
        self.tools.append(tool)

    def status(self):
        return f"Agent {self.name} 已装配 {len(self.tools)} 个工具"

tool = Tool("搜索")
agent = Agent("小K")
agent.add_tool(tool)

print(tool.describe())
print(agent.status())
"""

EXPECTED_OUTPUT = "工具：搜索\nAgent 小K 已装配 1 个工具"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, (
            "输出不对哦，期望打印两行：\n"
            "工具：搜索\nAgent 小K 已装配 1 个工具"
        )
    tree = ast.parse(source)
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    if "Tool" not in classes or "Agent" not in classes:
        return False, "结果对了，但本关要求定义 Tool 和 Agent 两个 class，不能直接打印答案"
    agent_methods = {
        node.name for node in classes["Agent"].body if isinstance(node, ast.FunctionDef)
    }
    missing = {"__init__", "add_tool"} - agent_methods
    if missing:
        return False, f"Agent 类还缺方法：{'、'.join(sorted(missing))}"
    return True, "过关！小K 有了对象形态，离真实框架又近一步。"
