# 第 23-28 关内容计划 · dsh 核心六包系列

> 已获用户批准。延续既有关卡模块约定与判题规范。
> 源码依据：`~/pyProjects/deepseek-harness`（TypeScript，浅克隆 MIT），调研报告已核对全部 file:line。
> 用户笔记：~/pyProjects/deepseek-harness-analysis/（章节 00-05），知识卡应与笔记章节互相引用。
> 注意：知识卡引用的 dsh 源码是 TypeScript——知识卡要点明"源码是 TS，我们用 Python 模仿它的机制"，TS 语法看不懂时引导用户查笔记里的《附录-TS语法速查》。

## 排序说明

用户提案顺序（按笔记章节 01-05）调整为**源码依赖顺序**：scope → session → tools → system-prompt → agent(inbox) → agent-loop（收口）。调研结论：agent-loop 依赖前面全部五包，是唯一适合收口的关；笔记章节映射不变，在知识卡里标出对应章节号。

## 共同约定

- 模块约定、判题规范（报错 → 输出 → ast 写法判定、中文人话、ast 不用子串匹配）与之前系列完全一致
- 全部离线，不需要 TIMEOUT
- 每关 tests/test_levelNN.py 3 用例：solution 过 / starter 不过 / 输出对写法不对的反例不过
- 系列内复用：第 24 关的 derive_messages 和第 27 关的 Inbox 会在第 28 关收口复用（starter 内置成品代码 + "这是你在第 N 关写的"注释，逐字一致）

---

## 第 23 关 · scope：分层可见性

- 剧情：agent 想有自己的"私人配置"——全局默认所有 agent 共享，但每个 agent 可以覆盖，互不干扰。
- 知识卡：
  - 源码位置：`packages/core/scope/src/store.ts:159`（`ScopedLayers`）+ `:208`（`merge`：近端 scope 覆盖远端）
  - 对应笔记章节：01-scope
  - Java 对照：Spring 的 Profile 覆盖 / 配置中心的多级覆盖——近端优先
  - 核心思想：一条父子链，读视图沿链继承，合并时近端 shadow 远端
- 任务：实现 `class ScopedLayers`：`register(name, value, scope=None)`（scope=None 是全局层）；`merge(scope)` 返回该 scope 视角的合并 dict（全局层 + 该 scope 层，scope 层覆盖同名全局项）。然后：全局注册 `("模型", "deepseek-chat")` 和 `("温度", 0.7)`；`"agent-A"` 层注册 `("温度", 0.1)`。打印 `merge("agent-A")` 的温度和 `merge("agent-B")` 的温度（B 没有覆盖，应看到全局值）。
- 期望输出：
  ```
  agent-A 的温度：0.1
  agent-B 的温度：0.7
  ```
- 判题：输出正确；ast 判定 ClassDef `ScopedLayers` 含 register 和 merge 方法；merge 内有覆盖逻辑（`update` 调用或字典解包）。

## 第 24 关 · session：事件日志与投影（重头戏）

- 剧情：dsh 最硬的铁律——"模型可见即已记录"。模型看到的一切先从 append-only 日志投影出来；回放、fork、恢复全部免费获得。
- 知识卡：
  - 源码位置：`packages/core/session/src/index.ts:724`（`deriveMessages()`）+ `surface.ts:83`（`deriveEventMessage()` 纯函数：user/message 原样、空 assistant 丢弃、其余忽略）
  - 对应笔记章节：04-session
  - Java 对照：事件溯源（Event Sourcing）——Axon Framework 同款思想；日志是事实，视图是投影
- 任务：给定事件列表 `log`（dict 列表，如 `{"type": "user/message", "content": "你好"}`、`{"type": "assistant/message", "content": ""}`（空内容！）、`{"type": "turn/start"}` 等）。玩家实现 `def derive_messages(log)`：遍历日志，`user/message` → `{"role": "user", "content": ...}`；`assistant/message` 且 content 非空 → `{"role": "assistant", ...}`（空 content 丢弃）；其他事件忽略。返回消息列表并逐条打印 `role: content`。
- 期望输出（log 里含一条空 assistant 和若干 turn/step 事件作为干扰项）：
  ```
  user: 你好
  assistant: 你好！我是小K
  user: 帮我查天气
  ```
- 判题：输出正确；ast 判定 `derive_messages` 含 For 循环和 If 分支（空内容判断）。

## 第 25 关 · tools：把关流水线与单调否决

- 剧情：工具注册谁都会写，dsh 的精髓在执行流水线：guard 只能否决、不能放行——所以无论注册顺序如何，安全规则都不可能被后来的规则"翻案"。
- 知识卡：
  - 源码位置：`packages/core/tools/src/index.ts:712`（`ToolGuard` 类型：返回字符串即否决，无 allow 形态）+ `:748`（`guardReason()`：第一个否决胜出）
  - 对应笔记章节：03-tool-calls / 05-tool-runtime
  - Java 对照：Spring Security 的投票器——但这里更狠，只有"反对票"存在
  - 单调性：安全性不依赖注册顺序，这是设计出来的，不是巧合
- 任务：实现 `class ToolRuntime`：`register(name, fn)`；`guard(fn)` 注册守卫（fn 收工具名，返回 None=不反对 或 字符串=否决理由）；`invoke(name)`：先依次问所有 guard，任一否决则返回 `已否决：{理由}`（第一个否决胜出，后续 guard 不问）；通过才真正调用工具并返回结果。注册工具 `"删除文件"`（返回 `已删除`），注册两个 guard：第一个对所有工具返回 None，第二个对 `"删除文件"` 返回 `高危操作`。调用 `"删除文件"` 并打印结果。
- 期望输出：`已否决：高危操作`
- 判题：输出正确；ast 判定 `invoke` 里 guard 循环在工具调用之前（函数体内 For 节点出现在工具调用的 Call 之前——可用 ast 节点位置 lineno 比较）；有短路逻辑（break 或 return）。

## 第 26 关 · system-prompt：段装注册表

- 剧情：第 16 关的 prompt 拼装是手写列表——dsh 升级成了注册表：片段带排序权重、scoped 覆盖同名全局片段、还能声明"本段独占全文"。
- 知识卡：
  - 源码位置：`packages/core/system-prompt/src/index.ts:518`（`assemble()`：合并 → 排序 → waterfall → complete 独占）
  - 对应笔记：整体架构 ② 节（`ctx.systemPrompt`）
  - Java 对照：Spring 的 `@Order` 注解 + Bean 覆盖
- 任务：实现 `class PromptAssembler`：`section(name, text, order)` 注册片段；`assemble()` 按 order 从小到大拼接（`\n\n` 连接）返回。注册三段：`("身份", "你是小K。", 1)`、`("工具", "可用工具：search", 2)`、`("风格", "回答要简短。", 0)`——注意"风格"order 最小应排最前。打印 assemble 结果。
- 期望输出：
  ```
  回答要简短。

  你是小K。

  可用工具：search
  ```
- 判题：输出正确（顺序是判定点）；ast 判定 `assemble` 里有排序（sorted 或 sort 调用）。

## 第 27 关 · agent/inbox：先写日志后改状态

- 剧情：agent 的收件箱随时可能崩。崩溃后怎么恢复？inbox 的每次变更先把"做了什么修改"记进事件日志，再改内存——重放日志就能复活。
- 知识卡：
  - 源码位置：`packages/core/agent/src/inbox.ts:25`（`class Inbox`）+ `:186-187`（先 append `agent/inbox/spliced` 事件再改内存投影）
  - 对应笔记：整体架构 ④ 节（输入统一走 inbox）；调研发现 inbox 在 agent 包而非 agent-loop 包
  - Java 对照：数据库 WAL（预写日志）——先写 redo log 再改数据页
  - 注意笔记归属修正：inbox 属于 core/agent，不是 core/agent-loop
- 任务：实现 `class Inbox`：内部有 `events`（事件日志列表）和 `queue`（内存列表）。`append(item)`：先往 events 记 `{"op": "add", "item": item}`，再改 queue；`claim()`：先记 `{"op": "remove", "item": 队首}`，再弹出并返回。`@classmethod replay(cls, events)`：从事件日志重建（add 入队、remove 移除）。操作：append "消息1"、"消息2"，claim 一次，打印 queue；然后用 `Inbox.replay(inbox.events)` 重建，打印重建后的 queue——两者必须相同。
- 期望输出：
  ```
  当前队列：['消息2']
  重放恢复：['消息2']
  ```
- 判题：输出正确；ast 判定 `append` 方法体内 events 的 append 调用出现在 queue 的 append 之前（用 lineno 比较）；有 classmethod replay。

## 第 28 关 · 收口：agent-loop 轮次状态机

- 剧情：总装关。ReAct 循环谁都能写个 while，dsh 的是状态机：turn 内反复 step，每个边界都落事件——这就是为什么它的会话能回放、能恢复、能 fork。
- 知识卡：
  - 源码位置：`packages/core/agent-loop/src/agent.ts:69`（`ReactLoopAgent`）+ `:253`（`turn()`）+ `:339`（`step()`）
  - 对应笔记章节：02-agent-loop（全仓核心单文件）
  - Java 对照：状态机模式；一轮 = 零到多个步骤，一个步骤 = 一次模型请求 + 它调用的工具
  - 收口提示：这个循环里 derive_messages 来自第 24 关、事件落账来自第 24 关的日志思想、工具执行可以接第 25 关的流水线
- 任务：starter 内置第 24 关的 `derive_messages` 成品代码（逐字一致）+ 一个脚本化 mock LLM：`mock_llm(messages)` 第一次返回 `{"content": "", "tool_calls": ["查天气"]}`，第二次返回 `{"content": "北京今天晴", "tool_calls": []}`；以及工具执行器 `run_tool(name)` 返回 `{"tool": name, "result": "晴 25°C"}`。玩家实现 `def agent_turn(log)`：append `turn/start`；循环：append `step/start` → 用 derive_messages 投影 log → 调 mock_llm → 把模型消息 append 为 `assistant/message` 事件 → 若有 tool_calls，逐个执行并把结果 append 为 `tool/result` 事件；没有 tool_calls 则 break；最后 append `turn/end`。执行后逐行打印日志的事件类型。
- 期望输出：
  ```
  turn/start
  step/start
  assistant/message
  tool/result
  step/start
  assistant/message
  turn/end
  ```
- 判题：输出逐行正确（事件序列是判定点）；ast 判定 `agent_turn` 含 While 循环和 break。
- 通关文案：六包全部到手——去读 dsh 真源码时，你会发现每个机制都见过。

---

## 实施与验收

- 批次 1：第 23-25 关；批次 2：第 26-28 关。各一个 commit
- 全量 `pytest tests/ -q --ignore=tests/e2e` 全绿
- 前端无需改动；完成后重启游戏服务
- 第 28 关 starter 内置的 derive_messages 必须与第 24 关 SOLUTION 逐字一致（审查程序化比对）
