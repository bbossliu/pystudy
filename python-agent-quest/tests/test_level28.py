from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 28)


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


def test_unrolled_loop_fails():
    # 输出正确，但把两个 step 写死成 for range(2)，没有 while 状态机和 break——不满足写法要求
    code = (
        "def derive_messages(log):\n"
        "    messages = []\n"
        "    for event in log:\n"
        "        if event[\"type\"] == \"user/message\":\n"
        "            messages.append({\"role\": \"user\", \"content\": event[\"content\"]})\n"
        "        elif event[\"type\"] == \"assistant/message\" and event[\"content\"]:\n"
        "            messages.append({\"role\": \"assistant\", \"content\": event[\"content\"]})\n"
        "    return messages\n"
        "\n"
        "_llm_calls = {\"n\": 0}\n"
        "\n"
        "def mock_llm(messages):\n"
        "    _llm_calls[\"n\"] += 1\n"
        "    if _llm_calls[\"n\"] == 1:\n"
        "        return {\"content\": \"\", \"tool_calls\": [\"查天气\"]}\n"
        "    return {\"content\": \"北京今天晴\", \"tool_calls\": []}\n"
        "\n"
        "def run_tool(name):\n"
        "    return {\"tool\": name, \"result\": \"晴 25°C\"}\n"
        "\n"
        "def agent_turn(log):\n"
        "    log.append({\"type\": \"turn/start\"})\n"
        "    for _ in range(2):\n"
        "        log.append({\"type\": \"step/start\"})\n"
        "        messages = derive_messages(log)\n"
        "        reply = mock_llm(messages)\n"
        "        log.append({\"type\": \"assistant/message\", \"content\": reply[\"content\"]})\n"
        "        for name in reply[\"tool_calls\"]:\n"
        "            result = run_tool(name)\n"
        "            log.append({\"type\": \"tool/result\", \"content\": result[\"result\"]})\n"
        "    log.append({\"type\": \"turn/end\"})\n"
        "\n"
        "log = []\n"
        "agent_turn(log)\n"
        "for event in log:\n"
        "    print(event[\"type\"])\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "while" in msg
