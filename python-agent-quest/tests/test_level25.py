from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 25)


def test_solution_passes():
    lv = _level()
    r = run_code(lv.solution)
    passed, msg = lv.judge(lv.solution, r)
    assert passed, msg


def test_starter_fails():
    lv = _level()
    r = run_code(lv.starter_code)
    passed, msg = lv.judge(lv.starter_code, r)
    assert not passed
    assert msg


def test_wrong_order_fails():
    # 输出正确，但 invoke 先调用工具再问 guard——顺序反了，不满足写法要求
    code = (
        "class ToolRuntime:\n"
        "    def __init__(self):\n"
        "        self.tools = {}\n"
        "        self.guards = []\n"
        "\n"
        "    def register(self, name, fn):\n"
        "        self.tools[name] = fn\n"
        "\n"
        "    def guard(self, fn):\n"
        "        self.guards.append(fn)\n"
        "\n"
        "    def invoke(self, name):\n"
        "        result = self.tools[name]()\n"
        "        for g in self.guards:\n"
        "            reason = g(name)\n"
        "            if reason is not None:\n"
        "                return f\"已否决：{reason}\"\n"
        "        return result\n"
        "\n"
        "runtime = ToolRuntime()\n"
        "runtime.register(\"删除文件\", lambda: \"已删除\")\n"
        "runtime.guard(lambda name: None)\n"
        "runtime.guard(lambda name: \"高危操作\" if name == \"删除文件\" else None)\n"
        "print(runtime.invoke(\"删除文件\"))\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "顺序反了" in msg
