# 第 35-41 关内容计划 · Python 基础补强系列 + 知识卡配图能力

> 已获用户批准（用户附加要求：注意排版 + 配图加强理解）。
> 体系依据：莫烦「交互式学Python」章节对照现有 34 关后的缺口（5.3 正则 / 8.3 复制 / 8.4 生成器 / 6.2 单测 / 5.2 目录管理 / 8.1 字符串 / 9.1 线程）。
> 砍掉：pickle、Tkinter、pip 管理、爬虫、编辑器（YAGNI）。

## 第一部分：配图引擎（前置任务）

- 关卡模块新增**可选**常量 `DIAGRAM`（mermaid 源码字符串）。loader 的 `Level` dataclass 加字段 `diagram: str | None = None`，与 TIMEOUT 同款可选读取；`REQUIRED_ATTRS` 不变。
- `/api/levels` 响应加 `"diagram": lv.diagram`。
- 前端（static/index.html）：引入 mermaid@10 CDN（`cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js`，`startOnLoad: false`，dark 主题）。showLevel 时：若当前关有 diagram，在知识卡下方渲染 `<pre class="mermaid">` 并调 `mermaid.run`；没有则隐藏图区。**降级**：mermaid 加载失败（CDN 不可达）时把 diagram 源码以等宽文本展示，不报错。
- e2e：test_smoke.py 补一条——打开一个带 DIAGRAM 的关，断言页面出现 mermaid 渲染的 `svg`。
- 旧关卡不动（后续想补图可单独提）。

## 第二部分：知识卡排版规范（本系列起生效）

统一五段式，段间空行、行宽 ≤ 50 字符：
```
1) 一句话点题（这个语法是什么/解决什么）
2) 核心用法（最小示例，2-4 行代码）
3) Java 对照（表格或对照行）
4) 坑与边界（Java 人最容易错的地方）
5) 延伸（对应莫烦章节号 / 何时用不上它）
有 DIAGRAM 的关：图说明一句话（"下图：……"）
```

## 第三部分：关卡内容

### 第 35 关 · 字符串方法族

- 剧情：agent 要解析用户输入的指令串。f-string 只是输出端，输入端的拆解靠方法族。
- 知识卡：split/join/strip/replace/startswith/切片；对照 Java `String.split`/`String.join`/`trim`/`startsWith`；坑：Python 字符串不可变，方法都返回新串（和 Java 一样）；莫烦 8.1。
- 任务：给定 `raw = "  查天气,北京,今天 "`。① strip 去首尾空格；② 按 `,` split 成列表；③ 打印列表第 2 项（`城市：北京`）；④ 把列表用 `|` join 打印（`查天气|北京|今天`）。
- 期望输出：
  ```
  城市：北京
  查天气|北京|今天
  ```
- 判题：输出正确；ast 判定 `.split` 和 `.join`（或 `.strip`）调用；无 DIAGRAM。

### 第 36 关 · 正则表达式

- 剧情：用户消息里混着工单号，格式是 `GD-` 加 6 位数字。把它抠出来——手写字符串解析会疯，正则一行搞定。
- 知识卡：`re.findall(r"GD-\d{6}", text)`；对照 Java `Pattern.compile` + `Matcher`（Python 的 re 是模块级直接用，不用先 compile）；坑：原始字符串 `r"..."` 不写的话 `\d` 会被转义；莫烦 5.3。
- DIAGRAM（可选，简单）：正则逐段含义标注（`GD-` 字面量 → `\d` 数字 → `{6}` 六次）。
- 任务：给定 `text = "用户说：工单 GD-102938 很急，另外 GD-000415 也看下，谢谢"`。用 re 找出所有工单号打印（`['GD-102938', 'GD-000415']`，直接 print 列表）。
- 期望输出：`['GD-102938', 'GD-000415']`
- 判题：输出正确；ast 判定 `re.findall`（或 re.search/finditer）调用。

### 第 37 关 · 浅拷贝与深拷贝（配图）

- 剧情：agent 把对话历史"复制"了一份做备份，结果改了备份，原件也变了——Java 人都懂这是引用，但 Python 的 `=`、浅拷贝、深拷贝三层语义和 Java 的对应关系值得掰开看。
- 知识卡：`b = a` 是贴新标签（≈ Java 引用赋值）；`list.copy()`/`[:]` 浅拷贝只复制外层；`copy.deepcopy` 全复制；坑：嵌套列表浅拷贝内层仍共享；对照 Java `clone()`/复制构造；莫烦 8.3。
- DIAGRAM（必配，graph LR）：`a` 和 `b` 两个标签指向同一个列表对象；浅拷贝后外层新对象、内层仍指向同一子列表。
- 任务：给定 `a = [[1, 2], [3, 4]]`。① 用 `copy.deepcopy` 复制出 `b`；② 修改 `b[0][0] = 99`；③ 打印 `a[0][0]`（应为 1）和 `b[0][0]`（应为 99）。
- 期望输出：
  ```
  原件：1
  副本：99
  ```
- 判题：输出正确；ast 判定 `deepcopy` 调用（用 `b = a` 或浅拷贝的反例必须拒）。

### 第 38 关 · 生成器（配图）

- 剧情：agent 要处理 100 万行日志，全读进内存会炸。生成器让数据"用多少来多少"——这也是 LLM 流式输出的底层思想。
- 知识卡：`yield` vs return（函数执行到 yield 暂停，下次从这里继续）；对照 Java Stream 的惰性求值/`Iterator.next()`；坑：生成器是一次性的，耗尽就没了；莫烦 8.4。
- DIAGRAM（必配，sequenceDiagram 或 graph）：调用方每次 next → 生成器产出一个值并暂停 → 再 next 再继续（对比普通函数一次性返回整个列表）。
- 任务：实现 `def read_logs()`：用 yield 依次产出 `"日志1"`, `"日志2"`, `"日志3"`（模拟逐行读）。然后用 for 消费，逐条打印 `读到：日志N`。
- 期望输出：
  ```
  读到：日志1
  读到：日志2
  读到：日志3
  ```
- 判题：输出正确；ast 判定函数内有 Yield 节点（返回列表的反例必须拒）。

### 第 39 关 · 文件目录管理

- 剧情：agent 的记忆文件攒了一堆在目录里。批量找出所有 `.json` 文件处理——别再 os.listdir 字符串拼路径了，pathlib 是现代写法。
- 知识卡：`Path.glob("*.json")`、`.name`、`.stem`；对照 `java.nio.file.Path`/`Files.walk`；坑：Windows/Mac 路径分隔符交给 pathlib；莫烦 5.2。
- 无 DIAGRAM。
- 任务：用代码先创建 3 个文件（`a.json`、`b.json`、`c.txt` 在当前目录——runner 的 workdir 隔离），然后用 pathlib 找出所有 `.json` 文件的文件名，排序后逐行打印。
- 期望输出：
  ```
  a.json
  b.json
  ```
- 判题：输出正确；ast 判定 `pathlib`/`Path` 使用 + `glob` 调用；judge 可检查 workdir 文件。

### 第 40 关 · 用 pytest 写单元测试

- 剧情：agent 代码越写越多，改一处怕坏三处。Java 人懂 JUnit，Python 这边是 pytest——断言更裸、参数化更爽。
- 知识卡：`assert` 直接断（vs JUnit `assertEquals`）；`@pytest.mark.parametrize`（vs `@ParameterizedTest`）；`pytest.raises`（vs `assertThrows`）；坑：测试文件名要 `test_` 开头；莫烦 6.2。
- 无 DIAGRAM。
- 任务（玩法特殊）：runner 单文件，所以任务是在一个文件里写"被测函数 + 测试函数 + 简易测试执行器"：实现 `def add(a, b)` 和 `def test_add()`（含 3 条 assert），starter 内置一个迷你 runner（遍历 `test_` 前缀函数执行并打印结果）。运行后打印 `test_add 通过`。
- 期望输出：`test_add 通过`
- 判题：输出正确；ast 判定有 `test_` 前缀函数且含 Assert 节点；备注：知识卡说明真实项目直接用 `pytest tests/`，本关用迷你 runner 演示机制。
- 备注：这是唯一一关"写测试"的关，判题重点在 assert 真的写了（Assert 节点 ≥ 3）。

### 第 41 关 · 线程与 GIL（配图）

- 剧情：Java 人的直觉：开 4 个线程算 4 份活，快 4 倍。Python 里试一下——咦，没快？这就是 GIL。
- 知识卡：`threading.Thread` vs Java `new Thread()` 几乎一样；GIL：同一时刻只有一个线程执行 Python 字节码（JVM 没有这东西）；IO 等待时 GIL 会释放（所以网络/文件 IO 多线程有效）；纯计算要快用多进程或 numpy；莫烦 9.1；呼应 L12：IO 并发也可以选 async。
- DIAGRAM（必配，graph）：时间轴上两个线程交替持有 GIL（对比 Java 双核真并行）。
- 任务：实现 `def worker(name, results)`：把 `f"{name} 完成"` append 进共享的 results 列表。起两个线程分别执行 `worker("线程A", results)` 和 `worker("线程B", results)`，join 等待，然后排序打印 results 每条。
- 期望输出（排序保证确定性）：
  ```
  线程A 完成
  线程B 完成
  ```
- 判题：输出正确；ast 判定 `threading.Thread` 调用和 `join` 调用。

---

## 实施与验收

- 批次 0（引擎）：DIAGRAM 字段 + 前端 mermaid + e2e 补图渲染断言 + 临时给一个既有关配 DIAGRAM 验证渲染（建议 L15 中间件洋葱图，验证后保留）
- 批次 1：第 35-37 关；批次 2：第 38-41 关
- 每关 tests/test_levelNN.py 3 用例（同既有规范）；引擎批次更新 e2e
- 全量 pytest 全绿；前端 mermaid CDN 加载失败降级为文本（e2e 环境有外网，验证正常渲染路径）
- 完成后重启游戏服务
