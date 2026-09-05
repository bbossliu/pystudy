# 造一个 Agent：Python 语法闯关游戏

## 启动

```bash
cd python-agent-quest
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn server.main:app
```

然后浏览器打开 http://127.0.0.1:8000 （需在 `python-agent-quest/` 目录下启动）。

## 测试

```bash
.venv/bin/pytest tests/
```

端到端测试需先安装浏览器：`.venv/bin/playwright install chromium`。
