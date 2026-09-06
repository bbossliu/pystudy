"""通关考试题库与判分。

答案（answer）和解析（explanation）只允许出现在 submit 的响应里，
GET /api/exam 返回的题目必须剥掉这两个字段——这是防泄漏红线。
每道题的代码类答案都用 venv 的 Python 实证过。
"""

PASSING_SCORE = 80
POINTS_PER_QUESTION = 5

QUESTIONS = [
    # ---- 语法系列（第 1-12 关），5 题 ----
    {
        "id": 1,
        "question": '执行下面代码，输出是什么？\n\nname = "小K"\nn = 3\nprint(f"{name}思考了{n * 2}轮")',
        "options": [
            "小K思考了6轮",
            "小K思考了{n * 2}轮",
            "小K思考了32轮",
            "语法错误，f-string 里不能写表达式",
        ],
        "answer": 0,
        "explanation": "f-string 的花括号里可以放任意表达式，n * 2 先算出 6 再拼进字符串，所以输出「小K思考了6轮」。选 B 是把花括号当成了纯文本；选 C 是误算了表达式；选 D 错在 f-string 完全支持内嵌表达式（这点和 Java 的 String.format 只填值不同）。",
        "level_id": 1,
    },
    {
        "id": 2,
        "question": '执行下面代码，输出是什么？\n\nmemory = ["你好"]\nbackup = memory\nbackup.append("在呢")\nprint(len(memory))',
        "options": ["1", "2", "3", "报错：list 没有 append 方法"],
        "answer": 1,
        "explanation": "backup = memory 不是复制，只是给同一个 list 起了第二个名字（别名）。对 backup 做 append 就等于改 memory，所以 len(memory) 是 2。想要真正的副本要用 memory.copy() 或 memory[:]。这正是 Agent 对话记忆共享时要小心的坑。",
        "level_id": 2,
    },
    {
        "id": 3,
        "question": 'msg = {"role": "user"}，执行 print(msg.get("content", "（空）")) 输出什么？',
        "options": ["None", "（空）", '报错 KeyError: "content"', '""（空字符串）'],
        "answer": 1,
        "explanation": "dict.get(key, default) 在 key 不存在时返回默认值「（空）」，不会抛异常。选 A 是没传默认值时 get 的行为；选 C 是 msg[\"content\"] 直接下标取值的行为。给 LLM 拼消息时，get 带默认值是读可选字段的安全姿势。",
        "level_id": 3,
    },
    {
        "id": 4,
        "question": "表达式 [x * x for x in range(5) if x % 2 == 1] 的结果是？",
        "options": ["[1, 9]", "[0, 4, 16]", "[1, 4, 9]", "[0, 1, 4, 9, 16]"],
        "answer": 0,
        "explanation": "推导式先 range(5) 得到 0~4，if x % 2 == 1 只留下奇数 1 和 3，再分别平方得到 [1, 9]。选 B 是把条件理解成了偶数；选 C 忘了过滤条件；选 D 既没过滤也没注意 range(5) 不含 5。",
        "level_id": 5,
    },
    {
        "id": 5,
        "question": '下面这段代码运行后（全程没有调用 weather()），会打印什么？\n\ndef register(fn):\n    print("注册:", fn.__name__)\n    return fn\n\n@register\ndef weather():\n    return "晴"',
        "options": [
            "注册: weather",
            "什么都不打印，因为 weather 没被调用",
            "晴",
            "报错：装饰器必须先调用才能生效",
        ],
        "answer": 0,
        "explanation": "@register 等价于 weather = register(weather)，在 def 语句执行的那一刻就跑了一次 register，所以打印「注册: weather」。装饰器是定义期执行的——@tool 自动注册靠的正是这个时机，不需要等函数被调用。",
        "level_id": 10,
    },
    # ---- 造 agent 系列（第 13-14 关），2 题 ----
    {
        "id": 6,
        "question": "一个最小 Agent 主循环（think → act）里，工具执行完后，结果应该怎么处理？",
        "options": [
            "追加到消息列表（对话记忆）里，再调 LLM 让它决定下一步",
            "直接 return 给用户，结束整个循环",
            "打印出来然后丢弃，不告诉 LLM",
            "存进一个全局变量，等程序退出时统一处理",
        ],
        "answer": 0,
        "explanation": "工具结果是 LLM 做下一轮决策的依据，必须以 tool/user 消息的身份追加进对话记忆，再调一次 LLM，否则模型根本不知道工具跑出了什么，循环就断了。选 B 会丢掉「观察结果再决策」的能力；C、D 都切断了信息回流。",
        "level_id": 13,
    },
    {
        "id": 7,
        "question": "用 openai SDK 接入 DeepSeek，正确的姿势是？",
        "options": [
            'OpenAI(base_url="https://api.deepseek.com", api_key=os.environ.get("DEEPSEEK_API_KEY"))',
            "把 API key 直接硬编码在源码里，方便部署",
            "DeepSeek 必须用专用 SDK，openai SDK 连不上",
            "messages 里的 role 字段只能填 user",
        ],
        "answer": 0,
        "explanation": "DeepSeek 兼容 OpenAI API，复用 openai SDK、只改 base_url 即可；key 必须从环境变量读，硬编码进源码一旦提交 git 就等于公开。role 还有 system（设定行为）和 assistant（模型回复）等，不只 user。",
        "level_id": 14,
    },
    # ---- deepagents 源码系列（第 15-22 关），4 题 ----
    {
        "id": 8,
        "question": "Deep Agents 的中间件洋葱模型：中间件 A 套 B 套 C，一次模型调用的请求与响应路径是？",
        "options": [
            "请求 A→B→C→LLM，响应 LLM→C→B→A",
            "请求 C→B→A→LLM，响应 LLM→A→B→C",
            "请求 A→B→C→LLM，响应 LLM→A→B→C",
            "三个中间件并行执行，顺序随机",
        ],
        "answer": 0,
        "explanation": "洋葱模型一层包一层：请求按注册顺序 A→B→C 往里钻，响应再逆序 C→B→A 出来，像 Java 的 Filter 链里 chain.doFilter() 前后的对称结构。选 B 方向反了；选 C 破坏了「先进后出」的对称性；选 D 错在中间件是嵌套调用，不是并行。",
        "level_id": 15,
    },
    {
        "id": 9,
        "question": "Deep Agents 为什么要定义 Backend 协议（read / write / edit / ls）并做出 StateBackend、FilesystemBackend、StoreBackend 多套实现？",
        "options": [
            "换存储实现（内存/文件/数据库）时不用改上层 agent 代码，测试用内存版、生产用文件版",
            "协议能自动加速文件读写",
            "Python 规定所有类都必须实现一个协议，否则无法运行",
            "为了让代码行数看起来更多",
        ],
        "answer": 0,
        "explanation": "这就是策略模式 / 面向接口编程：上层只依赖一组标准方法，背后是内存 dict 还是真实文件还是数据库完全不关心。测试用内存版快且不弄脏磁盘，生产换文件版，分布式换数据库版——换实现不改业务代码。",
        "level_id": 17,
    },
    {
        "id": 10,
        "question": "Deep Agents 派发 subagent 时，子代理的初始上下文是？",
        "options": [
            "只有一条描述任务的 HumanMessage，主对话历史一条都不带",
            "完整继承主对话的全部历史消息",
            "继承历史，但只保留 system 消息",
            "由主 agent 随机挑一半历史传过去",
        ],
        "answer": 0,
        "explanation": "这就是上下文隔离（context isolation）：子代理拿到的只有任务描述这一条消息。全量传历史既浪费 token 又干扰判断；隔离后子代理跑偏了也不污染主对话，它的中间过程主 agent 根本看不见，最后只有结果被包装成一条 tool 消息回来。",
        "level_id": 19,
    },
    {
        "id": 11,
        "question": "Deep Agents 的 Skills 渐进式披露（progressive disclosure）指的是？",
        "options": [
            "system prompt 里只放技能的名字+描述索引，模型声明要用某个技能时才去读它的完整文件",
            "把所有技能的全文一次性塞进 system prompt",
            "技能文件全部加密，运行时才解密",
            "每个技能各起一个子进程隔离运行",
        ],
        "answer": 0,
        "explanation": "先给目录、需要再取正文：索引只有几百 token，一百个技能的全文则是几万 token。这是「上下文里放引用，细节按需加载」的思想，和大结果落盘同源。选 B 恰恰是要避免的做法；C、D 与披露机制无关。",
        "level_id": 21,
    },
    # ---- dsh 六包系列（第 23-28 关），4 题 ----
    {
        "id": 12,
        "question": "dsh 的 scope 分层可见性里，父子 scope 链上出现同名配置时，谁生效？",
        "options": [
            "近端覆盖远端：离当前 scope 近的那份配置赢",
            "远端覆盖近端：全局默认永远优先",
            "同名配置直接报错，不允许出现",
            "两份配置的值做字符串拼接",
        ],
        "answer": 0,
        "explanation": "scope 沿父子链合并时近端 shadow 远端——同名配置离你近的那个赢，像 Spring 的 application-prod.yml 覆盖 application.yml。这样所有 agent 共享全局默认，每个 agent 只改自己在乎的几项，互不干扰。",
        "level_id": 23,
    },
    {
        "id": 13,
        "question": "dsh session 包的铁律「模型可见即已记录」意味着？",
        "options": [
            "模型看到的一切消息都先从 append-only 事件日志投影出来，状态 = 事件流的回放视图",
            "直接把当前对话状态存在一个大 dict 里，随用随改",
            "只有出错时才需要记日志",
            "日志只是给人看的，和模型看到的消息可以不一致",
        ],
        "answer": 0,
        "explanation": "这是事件溯源（Event Sourcing）：不直接存「当前状态」，而是存一串 append-only 事件，当前视图 = 把事件流 fold 出来。日志是事实，视图是投影——回放、fork、崩溃恢复全部免费获得。选 B、D 都让视图和事实可能脱节。",
        "level_id": 24,
    },
    {
        "id": 14,
        "question": "dsh tools 包的把关流水线为什么叫「单调否决」？",
        "options": [
            "guard 只能说「我反对」、没有「我批准」的形态，任一否决即拦下，与注册顺序无关",
            "所有 guard 必须投出全票赞成才能执行工具",
            "后注册的 guard 可以推翻前面 guard 的否决",
            "guard 只检查一次，通过后永久免检",
        ],
        "answer": 0,
        "explanation": "guard 返回字符串即否决，压根没有 allow 的形态——所以安全规则不可能被后来的规则「翻案」，这是设计出来的单调性，安全性不依赖注册顺序。选 C 描述的正是被杜绝的翻案；对比 Spring Security 的三态投票器，dsh 只有反对票。",
        "level_id": 25,
    },
    {
        "id": 15,
        "question": "dsh agent-loop 里 turn（轮）与 step（步骤）的关系是？",
        "options": [
            "一轮 turn = 零到多个 step；一个 step = 一次模型请求 + 它调用的工具；每个边界都落事件",
            "一轮 turn 有且只有一个 step",
            "step 包含多个 turn",
            "turn 和 step 是同义词，只是命名不同",
        ],
        "answer": 0,
        "explanation": "turn 是一轮对话的边界，模型可能连续调好几轮工具，所以一轮 = 零到多个 step；每个 step 是一次模型请求加它调用的工具。它是明确的状态机而不是大 while：turn 开始/结束、step 边界、模型消息、工具结果，每个边界都 append 一条事件，会话才能回放、恢复、fork。",
        "level_id": 28,
    },
    # ---- 数据处理系列（第 29-34 关），2 题 ----
    {
        "id": 16,
        "question": "import numpy as np 之后：\n\na = np.array([1, 2, 3])\nb = [1, 2, 3]\n\na * 2 和 b * 2 分别得到什么？",
        "options": [
            "a * 2 是逐元素翻倍 [2, 4, 6]；b * 2 是列表重复两遍 [1, 2, 3, 1, 2, 3]",
            "两个都是逐元素翻倍 [2, 4, 6]",
            "两个都是重复两遍",
            "a * 2 报错，ndarray 不能做乘法",
        ],
        "answer": 0,
        "explanation": "ndarray 的 * 是向量化逐元素运算，[1,2,3] * 2 = [2,4,6]；而 Python 原生 list 的 * 是重复拼接，[1,2,3] * 2 = [1,2,3,1,2,3]。同名运算符、两套语义，这正是从 list 换到 ndarray 时最先要建立的直觉。",
        "level_id": 29,
    },
    {
        "id": 17,
        "question": 'df 是含「城市」「销量」两列的 DataFrame，df.groupby("城市")["销量"].sum() 的结果是？',
        "options": [
            "按城市分组，对每组的销量求和，得到以城市为索引的 Series",
            "把所有行的销量加总成一个大数",
            "按销量排序后的新 DataFrame",
            "每个城市出现次数的计数",
        ],
        "answer": 0,
        "explanation": "groupby(\"城市\") 先按城市把行分成若干组，[\"销量\"] 选出销量列，sum() 对每组求和——结果是索引为城市、值为该城市总销量的 Series。比如北京 10+30=40、上海 20。选 B 漏了分组；选 C 是 sort_values；选 D 是 count。",
        "level_id": 34,
    },
    # ---- 基础补强系列（第 35-41 关），3 题 ----
    {
        "id": 18,
        "question": 'import re 之后，re.findall(r"\\d+", "工单A123和B45") 返回什么？',
        "options": [
            '["123", "45"]',
            '["A123", "B45"]',
            '"123"',
            '["工单A123和B45"]',
        ],
        "answer": 0,
        "explanation": "\\d+ 匹配「连续的一段数字」，findall 返回所有匹配段组成的列表：A123 里的 123 是一段，B45 里的 45 是一段，所以是 [\"123\", \"45\"]。选 B 把字母也圈进去了；选 C 是 re.search 拿到单个 Match 再 group 的形状，不是 findall。",
        "level_id": 36,
    },
    {
        "id": 19,
        "question": "执行下面代码，输出是什么？\n\nimport copy\na = [[1, 2], [3, 4]]\nb = copy.copy(a)\nb[0].append(99)\nprint(a[0])",
        "options": ["[1, 2, 99]", "[1, 2]", "报错", "[99]"],
        "answer": 0,
        "explanation": "copy.copy 是浅拷贝：外层列表是新的，但里面的子列表 [1, 2] 仍然和 a 共享同一个对象。改 b[0] 就等于改 a[0]，所以输出 [1, 2, 99]。想让嵌套结构也完全独立要用 copy.deepcopy——「备份别连累原件」说的就是这事。",
        "level_id": 37,
    },
    {
        "id": 20,
        "question": "关于 CPython 的 GIL（全局解释器锁），哪个说法对？",
        "options": [
            "同一时刻只有一个线程在执行 Python 字节码：CPU 密集任务开多线程提不了速，I/O 密集任务仍然受益",
            "多线程能让 CPU 密集任务随线程数线性加速",
            "GIL 会让多线程程序必然死锁",
            "I/O 等待时线程也一直占着 GIL 不放",
        ],
        "answer": 0,
        "explanation": "GIL 保证同一时刻只有一个线程执行字节码，所以 CPU 密集任务多线程帮不上忙（要多进程）；但线程在 I/O 等待（网络、磁盘）时会释放 GIL，所以 I/O 密集任务——比如并发调多个 LLM/工具——多线程仍然有效。写法眼熟，语义和 Java 完全不同。",
        "level_id": 41,
    },
]


def public_questions() -> list[dict]:
    """GET /api/exam 用：剥掉 answer/explanation/level_id，防泄漏。"""
    return [
        {"id": q["id"], "question": q["question"], "options": q["options"]}
        for q in QUESTIONS
    ]


def grade(answers: dict) -> dict:
    """判分：未作答按错；未知题目 id 直接忽略。"""
    results = []
    correct_count = 0
    for q in QUESTIONS:
        choice = answers.get(str(q["id"]))
        correct = choice == q["answer"]
        if correct:
            correct_count += 1
        results.append(
            {
                "id": q["id"],
                "your_choice": choice,
                "correct_choice": q["answer"],
                "correct": correct,
                "explanation": q["explanation"],
                "level_id": q["level_id"],
            }
        )
    score = correct_count * POINTS_PER_QUESTION
    return {
        "score": score,
        "passed": score >= PASSING_SCORE,
        "total": len(QUESTIONS),
        "results": results,
    }
