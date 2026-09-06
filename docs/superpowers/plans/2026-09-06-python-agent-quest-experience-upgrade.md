# 体验升级实施计划 · 高亮 / UI / AI 助教 / 通关考试

> 已获用户批准。四个批次顺序执行（都动 index.html，不可并行）。
> 前端仍是单 HTML 文件、不引框架；CDN 失败一律降级不白屏。

## 批次 1 · Markdown 渲染 + 代码高亮

- CDN：markdown-it + highlight.js（default dark 主题 css）。与 CodeMirror/mermaid 并列引入
- 知识卡渲染：`md.render(lv.knowledge)`，`md = markdownit({breaks: true, linkify: false, highlight: hljs 高亮函数})`；`breaks: true` 保证现有纯文本卡片换行不变
- **降级**：markdown-it 未加载时回退 textContent 纯文本（现状行为）
- 把 level01 的 KNOWLEDGE 重排为带 ``` 围栏代码块的 Markdown 格式，作为示范（其余 40 关保持纯文本，正常显示即可，不批量改）
- 测试：e2e 补一条——第 1 关知识卡中出现 highlight.js 产物（`.hljs` 元素）
- 不破坏既有元素 ID 与 e2e

## 批次 2 · UI 重做

布局（保持全部既有元素 ID 不变：#level-title #story #knowledge #diagram #parts #code #run-btn #output #message #progress，e2e 不能挂）：
- 顶栏：标题 + **进度条**（百分比填充，绿色）+ 进度文本；右侧预留「期末考试」按钮位（批次 4 用，本批先不放）
- 左侧 sidebar：关卡导航列表，可滚动、当前关高亮、已过关绿点、点击跳转（复用现有逻辑）；标题改为「关卡」
- 主区：剧情卡 → 知识卡 → 图 → 编辑器 → 运行按钮 → 输出 → 提示信息，卡片圆角/阴影/间距统一，字体排印（行高 1.7、代码字体 JetBrains Mono 或系统等宽）
- 运行按钮：点击后进入 loading 态（禁用 + 转圈），响应返回恢复
- 过关动效：进度条一次 0.3s 的亮度脉冲（CSS transition，克制）
- 侧边「我的 Agent 装配进度」卡并入 sidebar 顶部（显示进度条即可，不再单列）
- e2e 全过为准（选择器不变）；新增 UI 无自动化测试要求，手动浏览器验证截图目检

## 批次 3 · AI 助教聊天

**后端**（新文件 server/chat.py）：
- `PROVIDERS` 配置 dict：
  - `deepseek`：base_url `https://api.deepseek.com`，env key `DEEPSEEK_API_KEY`，models `["deepseek-chat", "deepseek-reasoner"]`
  - `glm`：base_url `https://open.bigmodel.cn/api/paas/v4`，env key `GLM_API_KEY`，models `["glm-4.7", "glm-4.7-flash", "glm-4.5-air"]`
- `available_providers()`：只返回 env key 已配置的提供商及其 models
- `GET /api/chat/providers` → `[{"id": "deepseek", "name": "DeepSeek", "models": [...]}, ...]`
- `POST /api/chat`，请求 `{provider, model, level_id, code, question}`：
  - 校验 provider 在已配置列表、model 在该 provider 的 models 里，否则 400 中文错误
  - 组装 system prompt：中文助教角色 + 当前关卡的 title/story/knowledge + 学生当前 code（从 level_id 查关卡内容，和 /api/run 同源）
  - messages = [system, user(question)]，调用 openai SDK（两个 provider 都是 OpenAI 兼容端点），返回 `{"reply": "..."}`
  - 超时 60s；API 报错返回 502 + 中文人话（含 401 特判"key 可能不对"）
- 不做流式（SSE 留作后续）；不做对话历史（每次单轮带关卡上下文，YAGNI）

**前端**：
- 右下角悬浮按钮「💬 问助教」→ 展开聊天面板（可折叠）
- 面板顶部两个下拉：提供商、模型（随提供商联动）；providers 为空时显示"未配置任何模型 key"提示
- 消息列表（助教回复走 Markdown 渲染）+ 输入框 + 发送按钮（发送中 loading 禁用）
- 发送时取当前 `levels[current]` 的 id 和 `editor.getValue()` 一起提交
- 对话历史只存内存（刷新清空）

**测试**：
- 单元：available_providers 的 env 过滤（monkeypatch）；POST /api/chat 的 400 校验（未知 provider/model）；500/502 错误路径（mock openai client 抛错）
- 真实 API：skipif 无 key 的真实 DeepSeek 调用用例（参照 level14 先例）
- 不泄露：任何响应/日志不含 key

## 批次 4 · 通关考试

**后端**（新文件 server/exam.py）：
- `QUESTIONS`：20 道选择题，字段 `{id, question, options: [4 个], answer: int, explanation: str, level_id: int}`
- 题目覆盖六个系列（语法 1-12 出 5 题、造 agent 13-14 出 2 题、deepagents 15-22 出 4 题、dsh 23-28 出 4 题、数据处理 29-34 出 2 题、基础补强 35-41 出 3 题），每题解析要点明"为什么对/错"，level_id 指向对应复习关
- `PASSING_SCORE = 80`，每题 5 分
- `GET /api/exam` → 题目列表（**不含 answer 和 explanation**）
- `POST /api/exam/submit`，请求 `{answers: {"1": 2, ...}}` → `{score, passed, total: 20, results: [{id, your_choice, correct_choice, correct: bool, explanation, level_id}]}`（含答对的题的解析，方便通读；未作答按错处理）
- 答案和解析永不出现在 GET 响应里

**前端**：
- 顶栏右侧「期末考试」按钮：进度未满时禁用（title 提示"通关全部关卡后解锁"），满 41 关点亮
- 点击进入考试视图（隐藏关卡区，显示试卷）：每题题干 + 4 个单选；底部「交卷」按钮（有未作答时二次确认）
- 成绩视图：大号分数 + 通过/未通过（≥80 过）+ 每题回顾：对错标记、你的选择、正确答案、**解析**、错题带「回到第 N 关复习」按钮（点击关闭考试视图并 showLevel 跳关）
- 「再考一次」按钮重新进试卷
- 最好成绩存 localStorage `quest_exam_best`，顶栏按钮上显示（如"期末考试 · 85"）
- 全部通过（考试通过）后成绩视图显示毕业文案

**测试**：
- 单元：全对 → 100 且 passed；全错 → 0 且每题含 explanation 和 level_id；部分对 → 分数正确；GET /api/exam 响应不含 answer/explanation 字段（负向断言，防泄漏）
- e2e 不新增（考试视图手动验证）

## 全局约束

- 所有新端点的错误文案中文人话
- 每批一个 commit；全量 pytest 全绿（e2e 只在引擎/前端批次跑）
- 四批全部完成后：重启游戏服务 + 用真实 DeepSeek key 手动 curl 验证 /api/chat 真实路径
