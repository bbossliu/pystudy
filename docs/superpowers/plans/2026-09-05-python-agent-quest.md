# 「造一个 Agent」Python 闯关游戏 — 垂直切片实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建可运行的最小闭环：FastAPI 判题后端 + 单页面前端 + 第 1 关内容 + 端到端冒烟测试。

**Architecture:** 浏览器单页面（无构建步骤）通过 HTTP 调用本地 FastAPI 服务；服务用 subprocess 隔离运行玩家代码（5 秒超时），再由每关的判题器断言结果。关卡是数据驱动的 Python 模块，后续 2-13 关只需新增关卡文件，不改引擎。

**Scope（重要）:** 本计划只做**垂直切片**（引擎 + 前端 + 第 1 关）。第 2-13 关是纯内容扩充，切片跑通后用后续计划批量添加——避免在引擎未验证前一次性写 13 关内容。

**Tech Stack:** Python 3.10.2、FastAPI、uvicorn、pytest、httpx（TestClient 依赖）、Playwright（e2e）、CodeMirror 5（CDN，前端代码编辑器）。

**Spec:** `docs/superpowers/specs/2026-09-05-python-agent-quest-design.md`

## Global Constraints

- Python 版本：3.10.2（`/Library/Frameworks/Python.framework/Versions/3.10/bin/python3`），代码可用 `list[X]`、`tuple[bool, str]` 等新式标注
- 项目目录：`python-agent-quest/`（仓库根目录下新建），所有命令在该目录内执行
- 虚拟环境：`.venv`，统一用 `.venv/bin/python`、`.venv/bin/pytest` 调用，避免依赖激活状态
- 用户代码运行限制：subprocess + 5 秒超时，运行目录为临时目录
- UI 文案全部中文；不使用真实 LLM API
- 前端为单个 HTML 文件，无构建步骤，不引入前端框架
- 每关判题器失败时必须给中文人话提示，不直接甩 traceback

---

### Task 1: 项目脚手架 + health 端点

**Files:**
- Create: `python-agent-quest/requirements.txt`
- Create: `python-agent-quest/.gitignore`
- Create: `python-agent-quest/server/__init__.py`（空文件）
- Create: `python-agent-quest/server/main.py`
- Test: `python-agent-quest/tests/test_api.py`

**Interfaces:**
- Produces: `server.main:app`（FastAPI 实例），`GET /api/health` 返回 `{"ok": True}`

- [ ] **Step 1: 创建目录、虚拟环境、依赖文件**

```bash
mkdir -p python-agent-quest/server/levels python-agent-quest/static python-agent-quest/tests/e2e
cd python-agent-quest
python3 -m venv .venv
```

`python-agent-quest/requirements.txt`：

```
fastapi>=0.110
uvicorn>=0.29
pytest>=8.0
httpx>=0.27
playwright>=1.44
```

`python-agent-quest/.gitignore`：

```
.venv/
__pycache__/
*.pyc
```

安装依赖：

```bash
cd python-agent-quest
.venv/bin/pip install -r requirements.txt
```

- [ ] **Step 2: 写失败的 API 测试**

`python-agent-quest/tests/test_api.py`：

```python
from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd python-agent-quest && .venv/bin/pytest tests/test_api.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'server'`）

- [ ] **Step 4: 写最小实现**

`python-agent-quest/server/__init__.py`：空文件。

`python-agent-quest/server/main.py`：

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/api/health")
def health():
    return {"ok": True}
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd python-agent-quest && .venv/bin/pytest tests/test_api.py -v`
Expected: PASS（1 passed）

- [ ] **Step 6: Commit**

```bash
git add python-agent-quest/
git commit -m "feat(quest): 项目脚手架 + health 端点"
```

---

### Task 2: 代码运行器 runner

**Files:**
- Create: `python-agent-quest/server/runner.py`
- Test: `python-agent-quest/tests/test_runner.py`

**Interfaces:**
- Produces: `run_code(source: str, timeout: int = 5) -> RunResult`；`RunResult` 为 dataclass，字段：`stdout: str, stderr: str, exit_code: int, timed_out: bool, workdir: str`（workdir 是本次运行的临时目录，判题器用来检查代码产出的文件）

- [ ] **Step 1: 写失败的测试**

`python-agent-quest/tests/test_runner.py`：

```python
import os

from server.runner import run_code


def test_run_code_captures_stdout():
    r = run_code("print('hello')")
    assert r.stdout.strip() == "hello"
    assert r.exit_code == 0
    assert not r.timed_out


def test_run_code_timeout():
    r = run_code("while True: pass", timeout=1)
    assert r.timed_out


def test_run_code_stderr_on_error():
    r = run_code("raise ValueError('boom')")
    assert r.exit_code != 0
    assert "ValueError" in r.stderr


def test_run_code_can_write_files_in_workdir():
    r = run_code("open('a.txt', 'w').write('hi')")
    assert os.path.exists(os.path.join(r.workdir, "a.txt"))
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd python-agent-quest && .venv/bin/pytest tests/test_runner.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'server.runner'`）

- [ ] **Step 3: 写实现**

`python-agent-quest/server/runner.py`：

```python
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass

DEFAULT_TIMEOUT = 5


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    workdir: str


def run_code(source: str, timeout: int = DEFAULT_TIMEOUT) -> RunResult:
    workdir = tempfile.mkdtemp(prefix="quest_")
    script = os.path.join(workdir, "main.py")
    with open(script, "w", encoding="utf-8") as f:
        f.write(source)
    try:
        proc = subprocess.run(
            [sys.executable, "main.py"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return RunResult(proc.stdout, proc.stderr, proc.returncode, False, workdir)
    except subprocess.TimeoutExpired:
        return RunResult("", "运行超时", -1, True, workdir)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd python-agent-quest && .venv/bin/pytest tests/test_runner.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: Commit**

```bash
git add python-agent-quest/server/runner.py python-agent-quest/tests/test_runner.py
git commit -m "feat(quest): subprocess 代码运行器（5 秒超时、临时目录）"
```

---

### Task 3: 关卡框架 loader + 第 1 关完整内容

**Files:**
- Create: `python-agent-quest/server/levels/__init__.py`（空文件）
- Create: `python-agent-quest/server/levels/loader.py`
- Create: `python-agent-quest/server/levels/level01.py`
- Test: `python-agent-quest/tests/test_levels.py`

**Interfaces:**
- Consumes: `server.runner.RunResult`、`run_code`
- Produces:
  - `load_levels() -> list[Level]`，按 `id` 升序
  - `Level` dataclass 字段：`id: int, title: str, story: str, knowledge: str, starter_code: str, solution: str, judge: JudgeFn`
  - `JudgeFn = Callable[[str, RunResult], tuple[bool, str]]`（参数为玩家源码和运行结果，返回是否通过 + 中文提示）
  - 关卡模块约定：`server/levels/levelNN.py`，必须含模块级常量 `ID, TITLE, STORY, KNOWLEDGE, STARTER_CODE, SOLUTION` 和函数 `judge(source: str, result: RunResult) -> tuple[bool, str]`

- [ ] **Step 1: 写失败的测试**

`python-agent-quest/tests/test_levels.py`：

```python
from server.levels.loader import load_levels
from server.runner import run_code


def test_loads_level01():
    levels = load_levels()
    assert len(levels) >= 1
    lv = levels[0]
    assert lv.id == 1
    assert "小K" in lv.story


def test_level01_judge_accepts_solution():
    lv = load_levels()[0]
    r = run_code(lv.solution)
    passed, _ = lv.judge(lv.solution, r)
    assert passed


def test_level01_judge_rejects_wrong_output():
    lv = load_levels()[0]
    code = 'name = "小K"\nrole = "代码助手"\nprint(f"我是{name}")'
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "输出不对" in msg


def test_level01_judge_rejects_non_fstring():
    lv = load_levels()[0]
    code = 'name = "小K"\nrole = "代码助手"\nprint("你是" + name + "，一个" + role + "。")'
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "f-string" in msg


def test_level01_judge_rejects_crashing_code():
    lv = load_levels()[0]
    code = "raise RuntimeError('boom')"
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "报错" in msg
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd python-agent-quest && .venv/bin/pytest tests/test_levels.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'server.levels'`）

- [ ] **Step 3: 写 loader**

`python-agent-quest/server/levels/__init__.py`：空文件。

`python-agent-quest/server/levels/loader.py`：

```python
import importlib
import pkgutil
from dataclasses import dataclass
from typing import Callable

from server.runner import RunResult

JudgeFn = Callable[[str, RunResult], "tuple[bool, str]"]

REQUIRED_ATTRS = ["ID", "TITLE", "STORY", "KNOWLEDGE", "STARTER_CODE", "SOLUTION", "judge"]


@dataclass
class Level:
    id: int
    title: str
    story: str
    knowledge: str
    starter_code: str
    solution: str
    judge: JudgeFn


def load_levels() -> list[Level]:
    import server.levels as pkg

    levels = []
    for info in pkgutil.iter_modules(pkg.__path__):
        if not info.name.startswith("level"):
            continue
        mod = importlib.import_module(f"server.levels.{info.name}")
        for attr in REQUIRED_ATTRS:
            if not hasattr(mod, attr):
                raise ValueError(f"关卡模块 {info.name} 缺少字段 {attr}")
        levels.append(
            Level(mod.ID, mod.TITLE, mod.STORY, mod.KNOWLEDGE,
                  mod.STARTER_CODE, mod.SOLUTION, mod.judge)
        )
    return sorted(levels, key=lambda lv: lv.id)
```

- [ ] **Step 4: 写第 1 关内容**

`python-agent-quest/server/levels/level01.py`：

```python
from server.runner import RunResult

ID = 1
TITLE = "变量与 f-string"

STORY = (
    "你的 agent 刚刚诞生，但它还不会自我介绍。给它拼一个 system prompt："
    "它叫「小K」，角色是「代码助手」。"
)

KNOWLEDGE = """\
Python 变量不需要声明类型：
  Java:   String name = "小K";
  Python: name = "小K"

f-string 是 Python 最常用的字符串拼接方式，在引号前加 f，变量直接写进 {}：
  Java:   String.format("你是%s，一个%s。", name, role)
  Python: f"你是{name}，一个{role}。"
"""

STARTER_CODE = """\
# 任务：定义变量 name 和 role，用 f-string 拼出 system prompt 并打印
# 期望输出：你是小K，一个代码助手。

name = ___  # 填：你的名字「小K」
role = ___  # 填：你的角色「代码助手」

system_prompt = ___  # 用 f-string 拼接 name 和 role
print(system_prompt)
"""

SOLUTION = """\
name = "小K"
role = "代码助手"
system_prompt = f"你是{name}，一个{role}。"
print(system_prompt)
"""

EXPECTED_OUTPUT = "你是小K，一个代码助手。"


def judge(source: str, result: RunResult) -> tuple[bool, str]:
    if result.exit_code != 0:
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知错误"
        return False, f"代码报错了：{last_line}"
    if EXPECTED_OUTPUT not in result.stdout:
        return False, f"输出不对哦，期望打印：{EXPECTED_OUTPUT}"
    if 'f"' not in source and "f'" not in source:
        return False, '结果对了，但本关要求用 f-string 拼接，试试 f"...{name}..." 的写法'
    return True, "过关！你的 agent 会自我介绍了。"
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd python-agent-quest && .venv/bin/pytest tests/test_levels.py -v`
Expected: PASS（5 passed）

- [ ] **Step 6: Commit**

```bash
git add python-agent-quest/server/levels/ python-agent-quest/tests/test_levels.py
git commit -m "feat(quest): 关卡加载框架 + 第 1 关（变量与 f-string）"
```

---

### Task 4: 关卡列表与判题 API

**Files:**
- Modify: `python-agent-quest/server/main.py`
- Test: `python-agent-quest/tests/test_api.py`（追加）

**Interfaces:**
- Consumes: `load_levels()`、`run_code`、`Level`
- Produces:
  - `GET /api/levels` → `[{"id": int, "title": str, "story": str, "knowledge": str, "starter_code": str}]`（**不含 solution**）
  - `POST /api/run`，请求体 `{"level_id": int, "code": str}` → `{"passed": bool, "stdout": str, "stderr": str, "message": str}`；未知 level_id 返回 404

- [ ] **Step 1: 追加失败的测试**

在 `python-agent-quest/tests/test_api.py` 末尾追加：

```python
def test_list_levels_hides_solution():
    resp = client.get("/api/levels")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["id"] == 1
    assert "starter_code" in data[0]
    assert "solution" not in data[0]


def test_run_endpoint_passes_with_solution():
    from server.levels.loader import load_levels

    solution = load_levels()[0].solution
    resp = client.post("/api/run", json={"level_id": 1, "code": solution})
    assert resp.status_code == 200
    assert resp.json()["passed"] is True


def test_run_endpoint_fails_with_starter_code():
    resp = client.post("/api/run", json={"level_id": 1, "code": "print('hi')"})
    assert resp.status_code == 200
    assert resp.json()["passed"] is False
    assert resp.json()["message"] != ""


def test_run_endpoint_404_for_unknown_level():
    resp = client.post("/api/run", json={"level_id": 999, "code": "pass"})
    assert resp.status_code == 404
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd python-agent-quest && .venv/bin/pytest tests/test_api.py -v`
Expected: FAIL（4 个新测试失败，404/405 类错误）

- [ ] **Step 3: 实现端点**

把 `python-agent-quest/server/main.py` 完整替换为：

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from server.levels.loader import load_levels
from server.runner import run_code

app = FastAPI()
LEVELS = {lv.id: lv for lv in load_levels()}


class RunRequest(BaseModel):
    level_id: int
    code: str


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/levels")
def list_levels():
    return [
        {
            "id": lv.id,
            "title": lv.title,
            "story": lv.story,
            "knowledge": lv.knowledge,
            "starter_code": lv.starter_code,
        }
        for lv in sorted(LEVELS.values(), key=lambda l: l.id)
    ]


@app.post("/api/run")
def run(req: RunRequest):
    lv = LEVELS.get(req.level_id)
    if lv is None:
        raise HTTPException(status_code=404, detail="关卡不存在")
    result = run_code(req.code)
    if result.timed_out:
        return {
            "passed": False,
            "stdout": "",
            "stderr": "",
            "message": "运行超时（超过 5 秒），检查是不是有死循环？",
        }
    passed, message = lv.judge(req.code, result)
    return {
        "passed": passed,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "message": message,
    }


@app.get("/")
def index():
    return FileResponse("static/index.html")
```

- [ ] **Step 4: 运行全部测试确认通过**

Run: `cd python-agent-quest && .venv/bin/pytest tests/test_api.py tests/test_levels.py tests/test_runner.py -v`
Expected: PASS（全部通过）

- [ ] **Step 5: Commit**

```bash
git add python-agent-quest/server/main.py python-agent-quest/tests/test_api.py
git commit -m "feat(quest): 关卡列表与判题 API（/api/levels、/api/run）"
```

---

### Task 5: 前端单页面

**Files:**
- Create: `python-agent-quest/static/index.html`
- 手动验证（本任务无自动化测试，e2e 在 Task 6 补上）

**Interfaces:**
- Consumes: `GET /api/levels`、`POST /api/run`、`GET /`（返回本页面）
- Produces: 页面全局暴露 `window.editor`（CodeMirror 实例，供 e2e 注入代码）；localStorage 键 `quest_progress`（已过关卡 id 数组）

- [ ] **Step 1: 写 index.html**

`python-agent-quest/static/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>造一个 Agent · Python 闯关</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/monokai.min.css">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "PingFang SC", sans-serif; background: #1e1e2e; color: #e0e0e0; }
  header { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: #181825; }
  header h1 { font-size: 18px; }
  #progress { font-size: 14px; color: #a6e3a1; }
  main { display: flex; gap: 16px; padding: 16px; height: calc(100vh - 54px); }
  #left { width: 38%; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
  #right { flex: 1; display: flex; flex-direction: column; gap: 8px; }
  .card { background: #313244; border-radius: 8px; padding: 14px 16px; }
  .card h2 { font-size: 16px; margin-bottom: 8px; color: #89b4fa; }
  .card h3 { font-size: 14px; margin-bottom: 8px; color: #f9e2af; }
  .card p, .card .body { font-size: 14px; line-height: 1.7; white-space: pre-wrap; }
  .part { list-style: none; font-size: 14px; padding: 3px 0; color: #6c7086; }
  .part.done { color: #a6e3a1; }
  .part::before { content: "○ "; }
  .part.done::before { content: "● "; }
  .CodeMirror { flex: 1; min-height: 300px; border-radius: 8px; font-size: 14px; }
  #run-btn { padding: 10px; font-size: 15px; border: none; border-radius: 8px; background: #89b4fa; color: #1e1e2e; cursor: pointer; font-weight: bold; }
  #run-btn:hover { background: #b4befe; }
  #output { background: #11111b; border-radius: 8px; padding: 10px; min-height: 60px; max-height: 160px; overflow-y: auto; font-size: 13px; white-space: pre-wrap; }
  #message { font-size: 14px; min-height: 22px; }
  #message.pass { color: #a6e3a1; }
  #message.fail { color: #f38ba8; }
</style>
</head>
<body>
<header>
  <h1>造一个 Agent · Python 闯关</h1>
  <div id="progress"></div>
</header>
<main>
  <section id="left">
    <div class="card"><h2 id="level-title"></h2><p id="story"></p></div>
    <div class="card"><h3>知识卡 · Java 对照</h3><div class="body" id="knowledge"></div></div>
    <div class="card"><h3>我的 Agent 装配进度</h3><ul id="parts"></ul></div>
  </section>
  <section id="right">
    <textarea id="code"></textarea>
    <button id="run-btn">运行</button>
    <pre id="output"></pre>
    <div id="message"></div>
  </section>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/python/python.min.js"></script>
<script>
let levels = [];
let current = 0;

const editor = CodeMirror.fromTextArea(document.getElementById("code"), {
  mode: "python", theme: "monokai", lineNumbers: true, indentUnit: 4,
});
window.editor = editor;

function getProgress() {
  return JSON.parse(localStorage.getItem("quest_progress") || "[]");
}

function saveProgress(id) {
  const p = getProgress();
  if (!p.includes(id)) {
    p.push(id);
    localStorage.setItem("quest_progress", JSON.stringify(p));
  }
}

async function loadLevels() {
  const resp = await fetch("/api/levels");
  levels = await resp.json();
  renderProgress();
  showLevel(0);
}

function showLevel(i) {
  current = i;
  const lv = levels[i];
  document.getElementById("level-title").textContent = "第 " + lv.id + " 关 · " + lv.title;
  document.getElementById("story").textContent = lv.story;
  document.getElementById("knowledge").textContent = lv.knowledge;
  editor.setValue(lv.starter_code);
  document.getElementById("output").textContent = "";
  document.getElementById("message").textContent = "";
}

function renderProgress() {
  const passed = getProgress();
  document.getElementById("progress").textContent =
    "进度 " + passed.length + "/" + levels.length;
  const ul = document.getElementById("parts");
  ul.innerHTML = "";
  levels.forEach(lv => {
    const li = document.createElement("li");
    li.className = "part" + (passed.includes(lv.id) ? " done" : "");
    li.textContent = lv.title;
    ul.appendChild(li);
  });
}

document.getElementById("run-btn").addEventListener("click", async () => {
  const lv = levels[current];
  const resp = await fetch("/api/run", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({level_id: lv.id, code: editor.getValue()}),
  });
  const data = await resp.json();
  document.getElementById("output").textContent =
    data.stdout + (data.stderr ? "\n" + data.stderr : "");
  const msg = document.getElementById("message");
  msg.textContent = data.message;
  msg.className = data.passed ? "pass" : "fail";
  if (data.passed) {
    saveProgress(lv.id);
    renderProgress();
    if (current + 1 < levels.length) {
      setTimeout(() => showLevel(current + 1), 1500);
    }
  }
});

loadLevels();
</script>
</body>
</html>
```

- [ ] **Step 2: 手动验证页面**

```bash
cd python-agent-quest
.venv/bin/uvicorn server.main:app --port 8000 &
sleep 2
curl -s http://127.0.0.1:8000/api/health
curl -s http://127.0.0.1:8000/ | head -5
```

Expected: health 返回 `{"ok":true}`；`/` 返回 HTML（首行为 `<!DOCTYPE html>`）。然后在浏览器打开 `http://127.0.0.1:8000`，确认页面渲染出第 1 关的剧情卡、知识卡、代码编辑器。验证后 `kill %1` 停掉服务。

- [ ] **Step 3: Commit**

```bash
git add python-agent-quest/static/index.html
git commit -m "feat(quest): 前端单页面（剧情卡/知识卡/编辑器/装配进度）"
```

---

### Task 6: Playwright 端到端冒烟测试

**Files:**
- Create: `python-agent-quest/tests/e2e/test_smoke.py`
- Test: 本文件即测试

**Interfaces:**
- Consumes: 运行中的服务（fixture 自动启动 uvicorn，端口 8123）、`window.editor`、第 1 关 solution

- [ ] **Step 1: 安装浏览器**

```bash
cd python-agent-quest
.venv/bin/playwright install chromium
```

- [ ] **Step 2: 写 e2e 测试**

`python-agent-quest/tests/e2e/test_smoke.py`：

```python
import json
import subprocess
import sys
import time
import urllib.request

import pytest
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8123"


@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app", "--port", "8123"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            urllib.request.urlopen(BASE + "/api/health", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    else:
        proc.terminate()
        pytest.fail("服务启动失败")
    yield proc
    proc.terminate()


def test_level1_pass_flow(server):
    from server.levels.loader import load_levels

    solution = load_levels()[0].solution
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE)
        page.wait_for_selector("#level-title")
        page.evaluate(f"editor.setValue({json.dumps(solution)})")
        page.click("#run-btn")
        page.wait_for_selector("#message.pass", timeout=10000)
        assert "过关" in page.inner_text("#message")
        browser.close()
```

- [ ] **Step 3: 运行 e2e 确认通过**

Run: `cd python-agent-quest && .venv/bin/pytest tests/e2e/test_smoke.py -v`
Expected: PASS（1 passed）

- [ ] **Step 4: 运行全部测试**

Run: `cd python-agent-quest && .venv/bin/pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add python-agent-quest/tests/e2e/
git commit -m "test(quest): Playwright 端到端冒烟（第 1 关通关流程）"
```

---

## Self-Review 记录

**Spec 覆盖：**
- 玩法四步（剧情卡/知识卡/任务/判题过关）→ Task 3（内容结构）+ Task 5（UI）✅
- Java 对照 → 每关 `KNOWLEDGE` 字段，第 1 关已示范 ✅
- FastAPI 后端、subprocess 5 秒超时 → Task 2、4 ✅
- 判题人话提示 → Task 3 judge 约定 + Global Constraints ✅
- 前端单 HTML、无框架、localStorage 进度 → Task 5 ✅
- pytest 判题器测试（正解过、错解挂）→ Task 3、4 ✅
- Playwright 冒烟 → Task 6 ✅
- **第 2-13 关、mock LLM 终关 → 明确留给后续内容计划**（切片验证后按 `levelNN.py` 模块约定批量新增，引擎无需改动）

**占位符扫描：** 无 TBD/TODO，所有代码步骤含完整代码。

**类型一致性：** `RunResult` 字段、`judge(source, result) -> tuple[bool, str]`、`load_levels() -> list[Level]`、`Level` 字段名在 Task 2/3/4/5/6 间一致；前端字段（id/title/story/knowledge/starter_code）与 `/api/levels` 响应一致；`window.editor` 在 Task 5 暴露、Task 6 使用，一致。
