from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 19)


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


def test_task_returning_string_fails():
    # 输出正确、task 也是两个参数，但返回的是字符串而不是 dict——不满足写法要求
    code = (
        "def subagent_run(description):\n"
        "    return f\"子代理完成：{description}\"\n"
        "\n"
        "def task(description, subagent_type):\n"
        "    return subagent_run(description)\n"
        "\n"
        "r = task(\"查一下天气\", \"weather-agent\")\n"
        "print(\"{'role': 'tool', 'content': '\" + r + \"'}\")\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "dict" in msg
