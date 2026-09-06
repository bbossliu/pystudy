# 第 15-22 关内容计划 · Deep Agents 源码精读系列

> 已获用户批准。延续 `2026-09-05-python-agent-quest-levels-2-13.md` 的模块约定与判题规范。
> 源码依据：`.superpowers/research/deepagents/libs/deepagents/deepagents/`（commit 见 git log，2026-09-05 clone）。

## 总原则

- **读源码学机制**：每关 KNOWLEDGE 必须标注对应的 deepagents 源码位置（file:line），鼓励学习者对照真源码
- **全部离线**：不 import deepagents 库（它要求 Python 3.11+，本项目 venv 是 3.10），不调用真实 LLM——用简化实现模仿核心机制
- 关卡模块约定不变：`ID, TITLE, STORY, KNOWLEDGE, STARTER_CODE, SOLUTION, judge` + 可选 `TIMEOUT`
- 判题：报错 → 输出 → ast 写法判定；失败文案中文人话
- 每关 tests/test_levelNN.py 3 用例：solution 过 / starter 不过 / 输出对但写法不对的反例不过

## 共同骨架说明

本系列关卡逐步搭建一个"迷你 deepagents"。第 15 关建立的中间件接口和第 17 关的 Backend 协议会在后续关卡复用——但**每关仍是独立文件**（runner 单文件限制），所以后续关卡的 STARTER_CODE 里以"已完成的前置代码"形式内置前面的成果（注释标明"这是你在第 N 关写的"），玩家只写本关新增部分。

---

## 第 15 关 · 中间件洋葱模型（地基关）

- 剧情：agent 功能越加越多，代码变成一锅粥。Deep Agents 的答案是中间件——每个功能都是包在 LLM 调用外的一层"洋葱皮"。
- 知识卡：
  - 源码位置：`middleware/__init__.py:15-47`，核心契约 `wrap_model_call(request, handler)`
  - Java 对照：Servlet Filter 链 / Spring Interceptor——`handler` 就是 `FilterChain.doFilter()`
  - 洋葱模型：请求一层层进，响应一层层出
- 任务：给定成品函数 `call_model(request)`（返回 `"LLM 回复"`）。玩家实现：`Middleware` 基类（`wrap_model_call(self, request, handler)` 默认直接调 handler）；`LogMiddleware`（调用前后各打印一行 `>> 进入 LogMiddleware` / `<< 离开 LogMiddleware`）；`run_with_middleware(request, middlewares)` 把中间件串成链。用 `[LogMiddleware()]` 跑一次并打印结果。
- 期望输出：
  ```
  >> 进入 LogMiddleware
  << 离开 LogMiddleware
  LLM 回复
  ```
- 判题：输出正确（注意顺序：打印在结果前）；ast 判定有 ClassDef `Middleware`、`run_with_middleware` 函数，且 LogMiddleware 的 wrap_model_call 调用了 handler。

## 第 16 关 · System prompt 分层组装

- 剧情：Deep Agents 的主 prompt 不是一坨字符串，而是分层的——基础 prompt + 各中间件注入的片段 + 工具描述。
- 知识卡：
  - 源码位置：`graph.py:639-648`（基础拼装）+ `middleware/_utils.py` 的 `append_to_system_message`
  - Java 对照：StringBuilder 链式拼接 / 模板引擎的片段组合
- 任务：给定 `BASE_PROMPT = "你是小K，一个代码助手。"`。玩家实现 `def build_prompt(base, injections)`：把 base 和 injections 列表里的片段用 `\n\n` 连接返回。然后用它拼：base + `["可用工具：search、read_file", "当前用户：小明"]`，打印结果。
- 期望输出：
  ```
  你是小K，一个代码助手。

  可用工具：search、read_file

  当前用户：小明
  ```
- 判题：输出正确；ast 判定有 `build_prompt` 函数定义（不接受手写整段字符串的玩法——用 ast 检查存在 join 调用或循环）。

## 第 17 关 · Backend 协议（策略模式）

- 剧情：上下文要落盘，但落到哪里——内存？本地文件？数据库？Deep Agents 的答案：定义统一协议，实现随便换。
- 知识卡：
  - 源码位置：`backends/protocol.py:404` 的 `BackendProtocol`（read/write/edit/ls…）
  - Java 对照：这就是接口 + 策略模式，Python 用鸭子类型连接口声明都省了
- 任务：实现 `class MemoryBackend`：`write(path, content)` 存进内部 dict、`read(path)` 取出、`ls()` 返回所有路径列表。写入 `"/notes/todo.txt"` 内容 `"买牛奶"`，打印 read 结果和 ls 结果。
- 期望输出：
  ```
  买牛奶
  ['/notes/todo.txt']
  ```
- 判题：输出正确；ast 判定 ClassDef `MemoryBackend` 含 write/read/ls 三个方法。

## 第 18 关 · 大结果落盘（offloading）

- 剧情：工具返回了 10MB 的日志，全塞进上下文会把模型撑爆。Deep Agents 的做法：超阈值就写进 backend，上下文里只留一个路径引用。
- 知识卡：
  - 源码位置：`filesystem.py:3241` 的 `_offload_tool_message_content`
  - Java 对照：大对象存 OSS 数据库只存 URL 的同款思路
- 任务：给定第 17 关的 `MemoryBackend` 成品代码（内置在 starter）。玩家实现 `def offload(content, backend, limit=20)`：content 长度 ≤ limit 直接返回 content；否则写入 backend（路径 `/offload/result.txt`）并返回 `[结果过大，已保存到 /offload/result.txt]`。分别用短字符串 `"小结果"` 和长字符串（`"很长的日志" * 10`）调用，打印两次返回值，最后打印 `backend.read("/offload/result.txt")` 的前 6 个字符。
- 期望输出：
  ```
  小结果
  [结果过大，已保存到 /offload/result.txt]
  很长的日志
  ```
- 判题：输出正确；ast 判定有 `offload` 函数且含 If 节点（长度判断）；判定 backend.write 被调用（ast 查 `.write` 调用）。

## 第 19 关 · Subagent 派发与上下文隔离

- 剧情：复杂任务来了，主 agent 想找个"临时工"帮忙。关键设计：子代理只拿到任务描述，看不到主对话——上下文隔离。
- 知识卡：
  - 源码位置：`subagents.py:732-794`（`_validate_and_prepare_state`：子代理只收到 `[HumanMessage(description)]`）
  - Java 对照：线程池提交任务——任务对象是全部输入；对比共享内存的线程
- 任务：给定成品 `subagent_run(description)`（模拟子代理，返回 `子代理完成：{description}`）。玩家实现 `def task(description, subagent_type)`：调用 `subagent_run(description)` 并把结果包装成 dict `{"role": "tool", "content": 结果}` 返回。调用 `task("查一下天气", "weather-agent")` 并打印返回的 dict。
- 期望输出：`{'role': 'tool', 'content': '子代理完成：查一下天气'}`
- 判题：输出正确；ast 判定 `task` 函数有两个参数、返回 Dict（ast.Dict 或 dict(...)）。

## 第 20 关 · 上下文压缩（summarization）

- 剧情：对话聊了 100 轮，上下文要炸了。Deep Agents 在用量到 85% 时触发压缩：旧消息变摘要，原文落盘可回溯。
- 知识卡：
  - 源码位置：`summarization.py:262`（触发阈值）+ `:734`（摘要替换历史）+ `:1189`（旧历史落盘）
  - Java 对照：JVM GC 的比喻——不是无限扩容，是回收整理
- 任务：给定 `MemoryBackend` 成品代码和 `fake_summarize(messages)`（把消息列表拼成一行摘要字符串）。玩家实现 `def compress(messages, backend, keep=2)`：把除最后 keep 条外的消息用 fake_summarize 汇总成一条 `{"role": "system", "content": "摘要：..."}`，旧消息原文写入 backend `/history/archive.txt`，返回 `[摘要消息] + 最后 keep 条`。用 4 条消息的列表调用，逐条打印返回结果的 content，最后打印 archive 里存了几条（提示：写入时一行一条，read 后按行数计数）。
- 期望输出：
  ```
  摘要：第一轮 第二轮
  第三轮
  第四轮
  归档了 2 条
  ```
  （输入消息为 `["第一轮", "第二轮", "第三轮", "第四轮"]`，fake_summarize 用空格连接）
- 判题：输出正确；ast 判定 `compress` 函数含切片（Subscript slice）操作；backend.write 被调用。

## 第 21 关 · Skills 发现与渐进式披露

- 剧情：agent 的技能不是写死在代码里的——Deep Agents 扫描目录里的 SKILL.md，只把"索引"（名字+描述）注入 prompt，模型需要时才读全文。
- 知识卡：
  - 源码位置：`skills.py:591`（扫描发现）+ `:905`（索引注入 prompt）
  - Java 对照：Spring 的类路径扫描 + 懒加载
  - 渐进式披露（progressive disclosure）：先给目录，需要再取正文，省 token
- 任务：给定 starter 内置的两个 skill 目录数据（用 dict 模拟文件系统：`SKILLS_FS = {"weather/SKILL.md": "---\nname: 查天气\ndesc: 查询城市天气\n---\n正文略", "stock/SKILL.md": "---\nname: 查股票\ndesc: 查询股票价格\n---\n正文略"}`）。玩家实现 `def discover_skills(fs)`：遍历 fs，解析每个 SKILL.md 的 name 和 desc（简单按行解析即可），返回索引字符串列表 `["- 查天气: 查询城市天气", ...]`；打印 `可用技能：` 后逐行打印索引。
- 期望输出：
  ```
  可用技能：
  - 查天气: 查询城市天气
  - 查股票: 查询股票价格
  ```
- 判题：输出正确；ast 判定 `discover_skills` 函数含 For 循环（遍历）和字符串解析（split 或 startswith 调用）。

## 第 22 关 · 收口：手写 create_my_deep_agent

- 剧情：所有机制都拆开来学过了。最后把它们装回去——写一个你自己的 `create_deep_agent`。
- 知识卡：
  - 源码位置：`graph.py:271`（`create_deep_agent`）+ `:956`（委托 create_agent）
  - Deep Agents 的真相：不是新引擎，是"预制装配厂"——模型 + prompt + 中间件栈 + 工具，按顺序组装
  - Java 对照：Spring Boot 的自动配置（auto-configuration）
- 任务：starter 内置第 15 关的中间件骨架和 `call_model`。玩家实现 `def create_my_deep_agent(middlewares)`：返回一个 `agent(request)` 函数（闭包），调用时先打印 `装配了 {n} 个中间件`（只在创建时打印一次），再用中间件链处理 request。用 `[LogMiddleware(), LogMiddleware()]` 创建 agent，调用 `agent("你好")` 并打印返回。
- 期望输出：
  ```
  装配了 2 个中间件
  >> 进入 LogMiddleware
  >> 进入 LogMiddleware
  << 离开 LogMiddleware
  << 离开 LogMiddleware
  LLM 回复
  ```
  （嵌套顺序体现洋葱模型：第一个进的后出）
- 判题：输出正确（顺序是关键）；ast 判定 `create_my_deep_agent` 内部有嵌套函数定义（闭包）或返回 lambda；通关文案：你读完了 Deep Agents 的核心骨架，接下来可以去读真源码/跑真库了。

---

## 实施与验收

- 批次 1：第 15-18 关；批次 2：第 19-22 关。各一个 commit
- 每关 3 个 pytest 用例；全量 `pytest tests/ -q --ignore=tests/e2e` 全绿
- 前端无需改动（关卡自动发现、可点击导航已有）
- 完成后重启游戏服务加载新关卡
- 复用约定：第 18、20 关复用第 17 关的 MemoryBackend（以"成品代码内置"形式写进 starter）；第 22 关复用第 15 关骨架。同一系列内代码必须前后一致
