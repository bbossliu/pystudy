from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 18)


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


def test_ternary_without_if_statement_fails():
    # 输出正确、也调用了 write，但用三元表达式代替 if 分支——不满足写法要求
    code = (
        "class MemoryBackend:\n"
        "    def __init__(self):\n"
        "        self.files = {}\n"
        "    def write(self, path, content):\n"
        "        self.files[path] = content\n"
        "    def read(self, path):\n"
        "        return self.files[path]\n"
        "    def ls(self):\n"
        "        return list(self.files.keys())\n"
        "\n"
        "def offload(content, backend, limit=20):\n"
        '    return content if len(content) <= limit else (\n'
        '        backend.write("/offload/result.txt", content)\n'
        '        or "[结果过大，已保存到 /offload/result.txt]"\n'
        "    )\n"
        "\n"
        "backend = MemoryBackend()\n"
        'print(offload("小结果", backend))\n'
        'print(offload("很长的日志" * 10, backend))\n'
        'print(backend.read("/offload/result.txt")[:5])\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "if" in msg
