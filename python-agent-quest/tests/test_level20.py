from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 20)


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


def test_loop_without_slice_fails():
    # 输出正确、也调用了 write，但用循环挑元素代替切片——不满足写法要求
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
        "def fake_summarize(messages):\n"
        "    return \" \".join(m[\"content\"] for m in messages)\n"
        "\n"
        "def compress(messages, backend, keep=2):\n"
        "    old = []\n"
        "    recent = []\n"
        "    for i, m in enumerate(messages):\n"
        "        if i < len(messages) - keep:\n"
        "            old.append(m)\n"
        "        else:\n"
        "            recent.append(m)\n"
        "    summary = {\"role\": \"system\", \"content\": \"摘要：\" + fake_summarize(old)}\n"
        "    backend.write(\"/history/archive.txt\", \"\\n\".join(m[\"content\"] for m in old))\n"
        "    return [summary] + recent\n"
        "\n"
        "messages = [\n"
        "    {\"role\": \"user\", \"content\": \"第一轮\"},\n"
        "    {\"role\": \"user\", \"content\": \"第二轮\"},\n"
        "    {\"role\": \"user\", \"content\": \"第三轮\"},\n"
        "    {\"role\": \"user\", \"content\": \"第四轮\"},\n"
        "]\n"
        "backend = MemoryBackend()\n"
        "for m in compress(messages, backend):\n"
        "    print(m[\"content\"])\n"
        "archived = backend.read(\"/history/archive.txt\")\n"
        "print(f\"归档了 {len(archived.splitlines())} 条\")\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "切片" in msg
