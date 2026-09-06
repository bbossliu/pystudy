# 第 29-34 关内容计划 · 数据处理系列（numpy / pandas）

> 已获用户批准。延续既有关卡模块约定与判题规范。
> 体系依据：莫烦 Python 数据处理线（numpy → pandas），知识卡标注对应莫烦章节号；数据集用 agent 场景（对话日志、工具调用记录）。
> 依赖：numpy 2.2.6 / pandas 2.3.3 已装入项目 venv，requirements.txt 需追加 `numpy`、`pandas`。

## 总原则

- 数据全部内联在代码里构造（runner 单文件限制），不读外部 CSV；第 31 关知识卡提一句 `pd.read_csv` 是真实项目的常态
- 输出必须确定性：凡打印浮点数，计划明确指定格式（如 `f"{x:.1f}"` 或转 int），判题按精确文本断言
- 模块约定、判题规范（报错 → 输出 → ast 写法判定、中文人话）与之前系列一致；写法判定围绕 numpy/pandas 调用（ast Attribute/Call 判定）
- 全部离线，不需要 TIMEOUT
- 每关 tests/test_levelNN.py 3 用例：solution 过 / starter 不过 / 输出对但写法不对的反例不过（反例：用纯 Python 循环/手写逻辑代替 numpy/pandas）

---

## 第 29 关 · ndarray 与向量化

- 剧情：你的 agent 上线一周了，攒了一批响应耗时数据。要算统计指标，别再用 for 循环一个个加了——numpy 一次搞定。
- 知识卡：
  - 对应莫烦章节：Numpy 1.3（和 List 的差别）/ 2.3（基础运算）
  - `np.array` vs Java 的 `int[]`：但 numpy 的运算符是整个数组的向量化操作（Java 要手写循环，Stream 也只是包装循环）
  - 向量化为什么快：底层 C 连续内存 + 无 Python 解释器开销
- 任务：给定耗时列表 `latencies = [120, 85, 340, 90, 1500, 200, 95]`（毫秒）。用 numpy：① 转成 ndarray；② 计算并打印均值（格式 `均值：{:.1f}`）；③ 全部耗时 +100（网络修正），打印修正后的最大值（格式 `修正后最大值：{}`，整数）。
- 期望输出：
  ```
  均值：347.1
  修正后最大值：1600
  ```
- 判题：输出正确；ast 判定调用了 `np.array`（或 `numpy.array`）且源码无 For 循环（逼向量化）。

## 第 30 关 · 维度、索引切片与 reshape

- 剧情：耗时数据按"天 × 小时"重新组织才有意义——把一维数据变二维矩阵，然后按行按列切着看。
- 知识卡：
  - 对应莫烦章节：Numpy 2.1（维度）/ 2.2（数据选择）/ 2.4（改变数据形态）
  - shape 概念 vs Java 二维数组 `int[3][4]`；reshape 不改数据只改"看法"
  - 切片 `arr[1, :]` vs Java 手取下标
- 任务：给定 `data = np.arange(12)`（0-11，模拟 3 天 × 4 个时段的调用次数）。① reshape 成 3 行 4 列并打印 shape（格式 `形状：(3, 4)`）；② 取第 2 行打印（`第 2 天：[4 5 6 7]`，直接 print 数组）；③ 取第 1 列打印（`时段 0：[0 4 8]`）。
- 期望输出：
  ```
  形状：(3, 4)
  第 2 天：[4 5 6 7]
  时段 0：[0 4 8]
  ```
- 判题：输出正确；ast 判定有 reshape 调用和 Subscript 切片（Slice 节点）。

## 第 31 关 · DataFrame 与数据选取

- 剧情：数组只能装数字，对话日志是"表格"——每行一条消息，每列一个字段。这就是 pandas 的主场。
- 知识卡：
  - 对应莫烦章节：Pandas 1.3（和 Numpy 差别）/ 2.2（数据是什么）/ 2.3（选取数据）
  - DataFrame vs Java 的 `List<Map<String, Object>>`（类型地狱）或一张 SQL 表
  - loc 按标签/条件选、iloc 按位置选；真实项目常用 `pd.read_csv(...)` 读文件，这里内联构造
- 任务：给定对话日志 dict（`{"轮次": [1,2,3,4], "角色": ["user","assistant","user","assistant"], "token数": [12, 156, 8, 203]}`）。① 构造 DataFrame；② 用 iloc 取第 1 行的角色打印（`第一条消息来自：user`）；③ 用 loc 取"角色"列等于 "assistant" 的行的"token数"列，打印均值（`assistant 平均 token：179.5`，格式 `{:.1f}`）。
- 期望输出：
  ```
  第一条消息来自：user
  assistant 平均 token：179.5
  ```
- 判题：输出正确；ast 判定 `pd.DataFrame`（或 `pandas.DataFrame`）构造 + loc 和 iloc 的 Attribute 使用。

## 第 32 关 · 条件筛选与基础统计

- 剧情：排查性能问题——把"慢对话"（token > 100）单独捞出来看统计。
- 知识卡：
  - 对应莫烦章节：Pandas 3.1（基础统计）/ 4.1（运算方法）
  - 布尔筛选 `df[df["token数"] > 100]` vs SQL `WHERE` / Java Stream `filter`
  - mean/max/min/sum 即 SQL 聚合函数
- 任务：沿用第 31 关的数据（starter 内置构造代码）。① 布尔筛选出 token 数 > 100 的行，打印行数（`慢对话条数：2`）；② 打印这些行的最大 token（`最慢的一条：203`）；③ 打印全表 token 总和（`总 token：379`）。
- 期望输出：
  ```
  慢对话条数：2
  最慢的一条：203
  总 token：379
  ```
- 判题：输出正确；ast 判定有布尔比较（Compare）用于 Subscript 筛选 + `.mean|.max|.sum` 中至少两个聚合调用。

## 第 33 关 · 缺失值与文字处理（数据清洗）

- 剧情：真实日志是脏的——有缺失的 token 数、大小写混乱的角色名。清洗是数据分析的第一步。
- 知识卡：
  - 对应莫烦章节：Pandas 4.2（文字处理）/ 4.3（异常数据处理）
  - NaN 处理：`fillna` 填充 / `dropna` 丢弃 vs Java Optional 或手写 null 检查
  - `.str` 访问器：整列字符串操作 vs Java `list.stream().map(String::toLowerCase)`
- 任务：给定脏数据（token数 含 None；角色 含 "User"、"USER"、"assistant" 等混乱大小写）。① 构造 DataFrame 后把"角色"列统一转小写；② "token数"列的缺失值用该列均值填充（fillna）；③ 打印清洗后"user"角色的条数（`user 条数：2`）和填充后的 token 总和（`清洗后总 token：417`，整数——数据：12, None, 8, None, 156, 203，均值 94.75，总和 12+94.75+8+94.75+156+203=568.5 → 实现者需重新设计数据使总和为整数，或改格式为 `{:.0f}`；以实现者自洽为准，但必须确定性）。
- 期望输出：由实现者按自洽数据确定并在报告中记录（要求：两条打印、数值确定）。
- 判题：输出正确；ast 判定 `.str` Attribute 使用 + `fillna` 或 `dropna` 调用。

## 第 34 关 · 收口：groupby 聚合分析

- 剧情：周报时间——按角色汇总对话量和 token 消耗，一张表看清 agent 的使用情况。
- 知识卡：
  - 对应莫烦章节：Pandas 5.2（Groupby）/ 5.1（Concat 和 Merge）
  - `groupby` vs SQL `GROUP BY` / Java `Collectors.groupingBy`——概念直接平移
  - split-apply-combine 三步思想
- 任务：给定一周对话日志（7 条，角色 user/assistant/tool 混合，含 token 数）。① 按角色 groupby，打印每个角色的平均 token（直接 print groupby 结果，pandas 输出格式固定）；② 打印 token 消耗最多的角色（`消耗最多：assistant`）。
- 期望输出：由实现者按自洽数据确定并在报告中记录（groupby 打印格式 pandas 固定，可精确断言）。
- 判题：输出正确；ast 判定 `groupby` 调用 + 聚合（`mean|sum|max|agg`）调用。

---

## 实施与验收

- requirements.txt 追加 numpy、pandas（已在 venv 装好 2.2.6 / 2.3.3，写 `numpy>=2.0`、`pandas>=2.0`）
- 批次 1：第 29-31 关；批次 2：第 32-34 关。各一个 commit
- 全量 `pytest tests/ -q --ignore=tests/e2e` 全绿
- 前端无需改动；完成后重启游戏服务
- 本系列各关数据独立（不做系列内代码复用要求），但第 32 关 starter 沿用第 31 关的数据集（保持"同一份日志连续分析"的叙事）
