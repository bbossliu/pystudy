# 第 2-13 关内容计划

> 依据 `docs/superpowers/specs/2026-09-05-python-agent-quest-design.md` 的关卡表。引擎已就绪（垂直切片已合并到 PR #1），本计划只做内容：每关一个 `server/levels/levelNN.py` + 一个 `tests/test_levelNN.py`，外加一个前端小改进。

**关卡模块约定（与 level01 完全一致，不得改名）：**
模块级常量 `ID, TITLE, STORY, KNOWLEDGE, STARTER_CODE, SOLUTION` + `def judge(source: str, result: RunResult) -> tuple[bool, str]`。

**内容要求（每关都必须满足）：**
- STORY：2-3 句中文剧情，把语法点包装成 agent 的需求，承接上一关
- KNOWLEDGE：语法讲解 + Java 对照（这是用户的核心诉求），以讲清为准，重点关（9、12）可以更长
- STARTER_CODE：含 `___` 占位符的半成品代码 + 注释说明任务和期望输出；直接运行必须失败（判题不通过）
- SOLUTION：完整可运行、能通过 judge 的答案
- judge：失败给中文人话提示，不甩 traceback；判定顺序：运行报错 → 输出对不对 → 写法符不符合本关要求
- **写法判定优先用 `ast` 模块解析源码**（终审结论：不要复制 level01 的子串匹配模式；level01 保持不动）
- RunResult.workdir 在 judge 调用期间有效（判题后才清理），可检查代码产出的文件

**每关测试（tests/test_levelNN.py）至少 3 个用例：**
1. solution 必须通过 judge
2. starter_code 必须不通过（且提示非空）
3. 一个"输出对但写法不对"的反例必须不通过（针对本关语法点）

---

## 第 2 关 · list：给 Agent 装对话记忆

- 剧情：agent 会自我介绍了，但每句话说完就忘。给它一个对话历史列表。
- 知识卡：list 对比 Java 的 `ArrayList`——不用声明泛型、直接 `append`；`len()` 对比 `.size()`。
- 任务：定义空列表 `messages`，依次 append 三条消息字符串（system 自我介绍、user 提问、assistant 回答），最后用 for 逐条打印（for 细节第 5 关才讲，这里给出打印循环的成品代码，玩家只管 append 部分）。
- 期望输出（逐行）：
  ```
  [system] 你是小K，一个代码助手。
  [user] 你能帮我写代码吗？
  [assistant] 当然可以！
  ```
- 判题：输出包含三行且顺序正确；ast 判定源码有 list 字面量或 `list()`，且调用了 `.append`。

## 第 3 关 · dict：消息要有结构

- 剧情：纯字符串消息分不清谁说的。把消息升级成结构化字典——这正是 OpenAI API 的消息格式。
- 知识卡：dict 对比 Java 的 `Map.of()` / HashMap——字面量直接写、键值访问用 `[]`；提一句 `{"role": "user", "content": "..."}` 就是真实 LLM API 的消息结构。
- 任务：构造一个 dict `message = {"role": "user", "content": "今天天气怎么样"}`，打印 `role` 和 `content` 两个字段。
- 期望输出：
  ```
  角色：user
  内容：今天天气怎么样
  ```
- 判题：输出正确；ast 判定源码含 Dict 节点且有用下标取值（Subscript）或 `.get(` 调用。

## 第 4 关 · if/elif：让 Agent 会做决定

- 剧情：agent 要能听懂用户想干嘛。给它装一个意图路由器。
- 知识卡：`if/elif/else` 对比 Java——冒号和缩进代替大括号；`in` 关键字判断包含（对比 `str.contains()`）；没有 switch（3.10 的 match 提一句即可，不作要求）。
- 任务：给定 `user_input = "帮我写个爬虫"`，用 if/elif/else 判断：含"写"→ 打印 `意图：写代码`；含"天气"→ `意图：查天气`；否则 `意图：闲聊`。
- 期望输出：`意图：写代码`
- 判题：输出正确；ast 判定源码有 If 节点且至少一个 elif（orelse 非空）；含 `in` 比较。

## 第 5 关 · for/while 与推导式：Agent 的思考循环

- 剧情：路由器有了。现在给 agent 装上主循环——think → act 的反复迭代，这是所有 agent 框架的核心。
- 知识卡：`for x in list` 对比 Java 增强 for；`while` 与 Java 相同；列表推导式 `[... for ... in ...]` 对比 Stream API 的 map/collect。
- 任务：给定 `steps = ["理解问题", "搜索资料", "生成回答"]`，① 用 for 带编号逐行打印（`步骤 1：理解问题`……，提示用 `enumerate`）；② 用列表推导式生成每步加上"完成"标记的新列表并打印。
- 期望输出：
  ```
  步骤 1：理解问题
  步骤 2：搜索资料
  步骤 3：生成回答
  ['理解问题-完成', '搜索资料-完成', '生成回答-完成']
  ```
- 判题：输出正确；ast 判定源码有 For 节点和 ListComp 节点。

## 第 6 关 · 函数：封装 LLM 调用

- 剧情：主循环每次都要拼凑调用逻辑，太乱。把"调用 LLM"封装成函数。
- 知识卡：`def` 对比 Java 方法——不用写返回类型；默认参数 `model="mock"` 对比 Java 方法重载；`return` 相同。提一句 Python 函数是一等公民（后面装饰器关用到）。
- 任务：定义 `def call_llm(prompt, model="mock-1")`：返回字符串 `[{model}] 回复：{prompt} 的模拟回答`。然后调用两次（一次带 model 参数 `"mock-pro"`，一次用默认值）并打印返回值。
- 期望输出：
  ```
  [mock-pro] 回复：你好 的模拟回答
  [mock-1] 回复：介绍一下你自己 的模拟回答
  ```
- 判题：输出正确；ast 判定有 FunctionDef `call_llm`，且有默认参数（defaults 非空）。

## 第 7 关 · 异常处理：工具调用会失败

- 剧情：agent 调工具时，外部世界不可靠——网络抖动、返回格式错误。不能一失败就崩溃。
- 知识卡：`try/except/finally` 对比 Java 的 try/catch——不用声明 throws；`except ValueError` 捕获指定异常对比 `catch (ValueException e)`；提一句"ask for forgiveness"是 Python 风格。
- 任务：给定 `raw_results = ["42", "abc", "7"]`（模拟工具返回），用 for + try/except 把每项转 int：成功打印 `结果：42`，失败打印 `跳过无效结果：abc`。
- 期望输出：
  ```
  结果：42
  跳过无效结果：abc
  结果：7
  ```
- 判题：输出正确；ast 判定有 Try 节点且 except 捕获 ValueError。

## 第 8 关 · 文件读写与 json：持久化记忆

- 剧情：程序一关，agent 的记忆就没了。把对话历史存到磁盘。
- 知识卡：`open()` + `with` 对比 Java try-with-resources；`json.dump/json.load` 对比 Jackson/Gson——标准库自带不用引依赖。
- 任务：把 `messages = [{"role": "user", "content": "你好"}]` 用 `json.dump` 写进 `memory.json`（注意 `ensure_ascii=False`）；再 `json.load` 读回来，打印 `已保存 1 条记忆`。
- 期望输出：`已保存 1 条记忆`
- 判题：输出正确；**检查 result.workdir 里 `memory.json` 真实存在且内容是合法 JSON、含 1 条记录**；ast 判定有 With 节点。

## 第 9 关 · class：Tool 与 Agent

- 剧情：功能越来越多，散装的变量和函数 hold 不住了。用类把 agent 和工具组织起来。
- 知识卡（重点关，Java 对比多写）：`class` 对比 Java——`__init__` 对比构造器；`self` 要显式写出来（Java 的 this 是隐式的）；不用写接口，duck typing；没有 private 关键字（约定 `_` 前缀）。
- 任务：定义 `class Tool`（`__init__` 收 name，`describe()` 返回 `工具：{name}`）；定义 `class Agent`（`__init__` 收 name，`add_tool(tool)`，`status()` 返回 `Agent {name} 已装配 1 个工具`）。创建一个 Tool("搜索") 装进 Agent("小K")，打印 describe 和 status。
- 期望输出：
  ```
  工具：搜索
  Agent 小K 已装配 1 个工具
  ```
- 判题：输出正确；ast 判定有两个 ClassDef（Tool、Agent），且 Agent 有 `__init__` 和 `add_tool`。

## 第 10 关 · 装饰器：@tool 注册

- 剧情：LangChain 里给函数加个 `@tool` 就能变成 agent 的工具，像魔法。拆开看这个魔法。
- 知识卡：装饰器对比 Java 注解——但 Python 装饰器是可执行的函数，不只是元数据；`@deco` 等价于 `func = deco(func)`；对比 Spring 的 `@Component` 自动注册。
- 任务：给定 `TOOL_REGISTRY = {}`，写装饰器 `def tool(func)`：把 `func.__name__ -> func` 注册进 TOOL_REGISTRY 后返回 func。用 `@tool` 装饰 `def search(query)`（返回 `搜索：{query}`）。打印 `已注册工具：['search']`（打印 `list(TOOL_REGISTRY.keys())`）并调用一次 search 打印结果。
- 期望输出：
  ```
  已注册工具：['search']
  搜索：Python 教程
  ```
- 判题：输出正确；ast 判定 `tool` 是 FunctionDef，且 `search` 的 decorator_list 含 `tool`。

## 第 11 关 · 模块与包：拆分项目

- 剧情：所有代码挤在一个文件里了。真实项目要拆模块——agent 项目通常分 `tools.py`、`agent.py`、`main.py`。
- 知识卡：`import` / `from ... import` 对比 Java 的 import + package；每个 .py 文件就是一个模块，不用显式导出；`__name__ == "__main__"` 对比 main 方法。
- 任务（在单文件里模拟拆模块）：先用代码把工具函数写进 `toolkit.py` 文件（`open("toolkit.py", "w").write(...)`，内容为一个 `def greet(name)` 返回 `你好，{name}`），然后 `import toolkit` 并打印 `toolkit.greet("小K")`。
- 期望输出：`你好，小K`
- 判题：输出正确；ast 判定有 Import 节点（导入 toolkit）；workdir 里 `toolkit.py` 存在。
- 备注：这是唯一一关"代码里写代码"，STORY 里要点明这是为了演示模块机制，真实项目是直接新建文件。

## 第 12 关 · async/await：并发调工具

- 剧情：agent 要同时查天气、搜资料、读文件，一个一个等太慢。异步让它同时开工。
- 知识卡（重点 Java 对比）：`async def` + `await` 对比 Java 的 CompletableFuture——但 Python 是单线程事件循环，不是多线程；`asyncio.gather` 对比 `CompletableFuture.allOf`；提一句"async 是 agent 框架的常态，LangChain/LangGraph 全是 async"。
- 任务：写 `async def call_tool(name)`：`await asyncio.sleep(0)`（模拟 IO），返回 `{name} 完成`。`async def main()` 里用 `await asyncio.gather(...)` 并发调用 `["查天气", "搜资料", "读文件"]`，逐行打印结果。最后 `asyncio.run(main())`。
- 期望输出（顺序固定为传入顺序）：
  ```
  查天气 完成
  搜资料 完成
  读文件 完成
  ```
- 判题：输出正确；ast 判定有 AsyncFunctionDef、Await、且调用了 `asyncio.gather` 与 `asyncio.run`。

## 第 13 关 · 终关：组装完整 Agent

- 剧情：所有零件都齐了。把它们组装成一个真正能跑的 agent，完成一次完整的对话。
- 知识卡：复习串联——本关没有新语法，看看你造的东西：prompt（L1）、记忆（L2/L3/L8）、路由（L4）、主循环（L5）、LLM 封装（L6）、容错（L7）、工具（L9/L10）、并发（L12）。接真实 API 只需把 mock_llm 换成 openai 调用。
- 任务（代码量最大，starter 给足骨架）：给定 `mock_llm(prompt)` 成品函数（返回 `mock 回复`）和 `TOOL_REGISTRY`，玩家完成 `class Agent`：`__init__(self, name)`（带空记忆列表）、`chat(self, user_input)`——把用户消息存进记忆（dict 形式）、调用 mock_llm 生成回复、把回复也存进记忆、返回回复。创建 agent，依次聊两句（"你好"、"记住我叫小明"），逐行打印 `用户：...` / `小K：...`，最后打印 `记忆条数：4`。
- 期望输出：
  ```
  用户：你好
  小K：mock 回复
  用户：记住我叫小明
  小K：mock 回复
  记忆条数：4
  ```
- 判题：输出正确；ast 判定有 ClassDef `Agent` 且含 `chat` 方法；源码中消息以 dict 形式（含 "role" 键）存取。
- 过关提示写一句庆祝语：agent 组装完成，可以接真实 API 了。

---

## 前端小改进：从第一个未通关卡开始

- 现状：`loadLevels()` 固定 `showLevel(0)`，13 关后老玩家每次从第 1 关开始。
- 改动：`showLevel` 的初始索引改为"第一个不在 quest_progress 里的关卡"，全通关则停在最后一关。约 3 行 JS。
- 无自动化测试要求（e2e 覆盖第 1 关流程，本改动不影响：清空 localStorage 时行为不变）。

## 测试与验收

- 每关 judge 的 3 个 pytest 用例（见上文）
- 全量 `.venv/bin/pytest tests/ -q` 全绿（现有 18 个 + 新增 36 个左右）
- e2e 不重写，复用现有 test_smoke.py（仍以第 1 关验证端到端）
- 分批提交：第 2-5 关 / 第 6-9 关 / 第 10-13 关 + 前端改进，各一个 commit
