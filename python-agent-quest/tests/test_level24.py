from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 24)


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


def test_comprehension_fails():
    # 输出正确，但用列表推导式一把梭，没有 for 循环和 if 分支——不满足写法要求
    code = (
        "def derive_messages(log):\n"
        "    role_map = {\"user/message\": \"user\", \"assistant/message\": \"assistant\"}\n"
        "    return [{\"role\": role_map[e[\"type\"]], \"content\": e[\"content\"]}\n"
        "            for e in log if e[\"type\"] in role_map and e[\"content\"]]\n"
        "\n"
        "log = [\n"
        "    {\"type\": \"turn/start\"},\n"
        "    {\"type\": \"user/message\", \"content\": \"你好\"},\n"
        "    {\"type\": \"assistant/message\", \"content\": \"你好！我是小K\"},\n"
        "    {\"type\": \"user/message\", \"content\": \"帮我查天气\"},\n"
        "    {\"type\": \"step/start\"},\n"
        "    {\"type\": \"assistant/message\", \"content\": \"\"},\n"
        "    {\"type\": \"tool/result\", \"content\": \"晴 25°C\"},\n"
        "    {\"type\": \"turn/end\"},\n"
        "]\n"
        "\n"
        "for msg in derive_messages(log):\n"
        "    print(f\"{msg['role']}: {msg['content']}\")\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "for 循环" in msg
